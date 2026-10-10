import bpy
import struct
import math
from mathutils import Matrix

ROT_FIX = Matrix.Rotation(-math.pi / 2, 4, 'Z')
ROT_FIX_INV = ROT_FIX.inverted()


def _write_uint8(file, v):  file.write(struct.pack('<B', v))
def _write_uint16(file, v): file.write(struct.pack('<H', v))
def _write_uint32(file, v): file.write(struct.pack('<I', v))

def _write_string(file, s):
    encoded = s.encode('ascii') + b'\x00'
    _write_uint16(file, len(encoded))
    file.write(encoded)


def _choose_precision(values):
    """Pick the highest precision bits (14 down to 8) where all values still fit in int16.
    Mirrors the scale formula from read_16bit_fixed_point_float:
      scale = 32767.0 / (2 ** (15 - precision_bits))
    A value fits when abs(value) * scale <= 32767, i.e. abs(value) <= 2 ** (15 - bits).
    """
    max_abs = max(abs(v) for v in values) if values else 0.0
    for bits in range(14, 7, -1):
        if max_abs <= 2 ** (15 - bits):
            return bits
    return 8


def _encode_channel(values, precision_bits):
    """Encode a list of floats as a 16-bit fixed-point RLE stream.

    Each block:
      byte 0 (tmp):            high bit = is_rle, low 7 bits = num_frames_in_block
      byte 1 (sub_block_size): int16 count for this block (header + values)
      RLE (constant):  sub_block_size = 2,               1 int16 value follows
      per-frame:       sub_block_size = num_frames + 1,  num_frames int16 values follow
    """
    scale = 32767.0 / (2 ** (15 - precision_bits))
    raw = [max(-32767, min(32767, round(v * scale))) for v in values]

    data = bytearray()
    i = 0
    while i < len(raw):
        j = i + 1
        while j < len(raw) and raw[j] == raw[i] and (j - i) < 127:
            j += 1

        if j - i > 1:  # constant run — write RLE block
            n = j - i
            data += struct.pack('<BBh', 0x80 | n, 2, raw[i])
        else:           # per-frame block (up to 127 frames)
            j = min(i + 127, len(raw))
            n = j - i
            data += struct.pack(f'<BB{n}h', n, n + 1, *raw[i:j])

        i += n

    return data


def export_baf(filepath, armature_obj, action=None, scene_scale=1.0):
    armature = armature_obj.data

    if action is None:
        if not armature_obj.animation_data or not armature_obj.animation_data.action:
            raise Exception("No action on armature")
        action = armature_obj.animation_data.action

    frame_start = int(action.frame_range[0])
    frame_end   = int(action.frame_range[1])
    num_frames  = frame_end - frame_start + 1

    # Collect animated bone names from action fcurves
    animated_names = set()
    for fc in action.fcurves:
        if fc.data_path.startswith('pose.bones["'):
            animated_names.add(fc.data_path.split('"')[1])

    animated_bones = [b for b in armature.bones if b.name in animated_names]
    if not animated_bones:
        raise Exception("No animated bones found in action")

    # Sample pose at every frame
    scene = bpy.context.scene
    prev_frame  = scene.frame_current
    prev_action = armature_obj.animation_data.action if armature_obj.animation_data else None
    armature_obj.animation_data.action = action

    # 7 channels per bone: qx qy qz qw tx ty tz
    channels = {b.name: [[] for _ in range(7)] for b in animated_bones}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        for bone in animated_bones:
            pb = armature_obj.pose.bones[bone.name]

            # Armature-space engine matrix for this bone (and its parent if any)
            eng_abs = pb.matrix @ ROT_FIX_INV
            if bone.parent:
                parent_pb = armature_obj.pose.bones.get(bone.parent.name)
                if parent_pb:
                    parent_eng_abs = parent_pb.matrix @ ROT_FIX_INV
                    anim_local = parent_eng_abs.inverted() @ eng_abs
                else:
                    anim_local = eng_abs
            else:
                anim_local = eng_abs

            blender_q = anim_local.to_3x3().to_quaternion()
            # Conjugate: engine uses row-vector convention
            ch = channels[bone.name]
            ch[0].append(-blender_q.x)
            ch[1].append(-blender_q.y)
            ch[2].append(-blender_q.z)
            ch[3].append( blender_q.w)
            tx, ty, tz = anim_local.translation / scene_scale
            ch[4].append(tx)
            ch[5].append(ty)
            ch[6].append(tz)

    # Restore state
    scene.frame_set(prev_frame)
    if armature_obj.animation_data and prev_action:
        armature_obj.animation_data.action = prev_action

    # Choose translation precision from data range
    all_trans = []
    for bone in animated_bones:
        for i in range(4, 7):
            all_trans.extend(channels[bone.name][i])
    precision = _choose_precision(all_trans)

    with open(filepath, 'wb') as f:
        _write_uint32(f, 3)  # version
        _write_uint16(f, len(animated_bones))
        for bone in animated_bones:
            _write_string(f, bone.name)
        _write_uint32(f, num_frames)
        _write_uint8(f, precision)

        for bone in animated_bones:
            ch = channels[bone.name]
            streams = []
            for i in range(4):  # rotation channels: precision 15
                streams.append(_encode_channel(ch[i], 15))
            for i in range(4, 7):  # translation channels: auto precision
                streams.append(_encode_channel(ch[i], precision))

            total_int16 = sum(len(s) // 2 for s in streams)
            _write_uint16(f, total_int16)  # streamCount

            for stream in streams:
                _write_uint16(f, len(stream) // 2)  # channel int16 count
                f.write(stream)
