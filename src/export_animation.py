import bpy
import struct

from .misc import *


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
    frame_end = int(action.frame_range[1])
    num_frames = frame_end - frame_start + 1

    animated_names = set()
    for fc in action.fcurves:
        if fc.data_path.startswith('pose.bones["'):
            animated_names.add(fc.data_path.split('"')[1])

    animated_bones = [b for b in armature.bones if b.name in animated_names]
    if not animated_bones:
        raise Exception("No animated bones found in action")

    root_frame = root_turn(b.name for b in armature.bones if b.parent is None).to_4x4() @ ROT_FIX
    pose_bones = armature_obj.pose.bones

    scene = bpy.context.scene
    prev_frame = scene.frame_current
    prev_action = armature_obj.animation_data.action if armature_obj.animation_data else None
    armature_obj.animation_data.action = action

    # 7 channels per bone: qx qy qz qw tx ty tz
    channels = {b.name: [[] for _ in range(7)] for b in animated_bones}
    last_rot = {}

    for frame in range(frame_start, frame_end + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()

        for bone in animated_bones:
            pose = pose_bones[bone.name].matrix
            if bone.parent:
                frame_local = pose_bones[bone.parent.name].matrix.inverted() @ pose
            else:
                frame_local = root_frame.inverted() @ pose
            engine_local = BONE_FRAME @ frame_local @ BONE_FRAME_INV

            rot = engine_local.to_3x3().to_quaternion()
            if bone.name in last_rot and rot.dot(last_rot[bone.name]) < 0:
                rot.negate()
            last_rot[bone.name] = rot.copy()

            ch = channels[bone.name]
            ch[0].append(-rot.x)
            ch[1].append(-rot.y)
            ch[2].append(-rot.z)
            ch[3].append(rot.w)
            tx, ty, tz = engine_local.translation / scene_scale
            ch[4].append(tx)
            ch[5].append(ty)
            ch[6].append(tz)

    scene.frame_set(prev_frame)
    if armature_obj.animation_data:
        armature_obj.animation_data.action = prev_action

    all_trans = []
    for bone in animated_bones:
        for i in range(4, 7):
            all_trans.extend(channels[bone.name][i])
    precision = _choose_precision(all_trans)

    with open(filepath, 'wb') as f:
        write_uint32(f, 3)  # version
        write_uint16(f, len(animated_bones))
        for bone in animated_bones:
            write_string(f, bone.name)
        write_uint32(f, num_frames)
        write_uint8(f, precision)

        for bone in animated_bones:
            ch = channels[bone.name]
            streams = [_encode_channel(ch[i], 15) for i in range(4)]
            streams += [_encode_channel(ch[i], precision) for i in range(4, 7)]
            write_uint16(f, sum(len(s) // 2 for s in streams))  # streamCount
            for stream in streams:
                write_uint16(f, len(stream) // 2)  # channel int16 count
                f.write(stream)
