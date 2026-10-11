import bpy
import math
import struct
from mathutils import Matrix, Quaternion, Vector

ROT_FIX = Matrix.Rotation(-math.pi / 2, 4, 'Z')
# Engine bone-local frame -> Blender bone-local frame (Y↔Z world swap, then ROT_FIX).
BONE_FRAME = Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0))).to_4x4() @ ROT_FIX
BONE_FRAME_INV = BONE_FRAME.inverted()
# Must match the Bip01 root turn in import_skeleton.py.
PLAYER_WORLD_FIX = Matrix.Rotation(-math.pi / 2, 4, 'X')

def read_float(file):
    return struct.unpack('<f', file.read(4))[0]

def read_uint8(file):
    return struct.unpack('<B', file.read(1))[0]

def read_int16(file):
    return struct.unpack('<h', file.read(2))[0]

def read_uint16(file):
    return struct.unpack('<H', file.read(2))[0]

def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]

def read_string(file, length):
    return file.read(length).decode('utf-8')

def read_16bit_fixed_point_float(file, precision_bits):
    """
    Reads a 16-bit value from file and decodes it as a float using a custom mantissa precision.

    Args:
        file: file-like object positioned at the custom float.
        precision_bits: number of bits used for the mantissa (e.g., 14).

    Returns:
        float: Decoded float value.
    """
    
    raw = read_int16(file)
    scale = 32767.0 / (2 ** (15 - precision_bits))
    return raw / scale

def tell_remaining_length(file):
    current_pos = file.tell()
    file.seek(0, 2)
    end_pos = file.tell()
    file.seek(current_pos)
    return end_pos - current_pos


class Bf1942Bone:
    def __init__(self, name):
        self.name = name
        self.frames = []  # list of (Quaternion, Vector) per frame


def parse_baf(filepath):
    bones = []
    with open(filepath, 'rb') as file:
        header = read_uint32(file)
        if header != 3:
            raise Exception(f"Unsupported .baf version {header}")

        num_bones = read_uint16(file)
        for _ in range(num_bones):
            name_len = read_uint16(file)
            name = read_string(file, name_len)[:-1]  # zero terminated
            bones.append(Bf1942Bone(name))

        num_frames = read_uint32(file)
        precision = read_uint8(file)

        for bone in bones:
            read_uint16(file)  # num_data (unused)
            bone_channels = [[] for _ in range(7)]  # channels: x,y,z,w rot + x,y,z pos

            for i in range(7):
                block_data_size = read_uint16(file)
                data_left = block_data_size
                total_frames = 0

                while data_left > 0:
                    tmp = read_uint8(file)
                    num_frames_in_block = tmp & 0b01111111
                    is_rle = (tmp >> 7) == 1
                    sub_block_size = read_uint8(file)
                    total_frames += num_frames_in_block
                    data_left -= sub_block_size

                    if is_rle:
                        val = read_16bit_fixed_point_float(file, 15 if i <= 3 else precision)
                        bone_channels[i].extend([val] * num_frames_in_block)
                    else:
                        for _ in range(num_frames_in_block):
                            val = read_16bit_fixed_point_float(file, 15 if i <= 3 else precision)
                            bone_channels[i].append(val)

                if total_frames != num_frames:
                    raise Exception(
                        f"Bone '{bone.name}' channel {i} has {total_frames} frames, expected {num_frames}"
                    )

            # Channels: [qx, qy, qz, qw, tx, ty, tz] in engine space.
            # The stored quaternion uses row-vector convention, so its conjugate is the column-vector rotation.
            for qx, qy, qz, qw, tx, ty, tz in zip(*bone_channels):
                rot = Quaternion((qw, -qx, -qy, -qz))
                pos = Vector((tx, ty, tz))
                bone.frames.append((rot, pos))

        data_left = tell_remaining_length(file)
        if data_left != 0:
            raise Exception(f"{data_left} unexpected bytes remaining at end of file")

    return bones


def apply_animation(armature_obj, bones, action_name="BF1942Anim", scene_scale=1.0):
    """Apply parsed .baf animation to an armature object."""
    armature = armature_obj.data
    pose_bones = armature_obj.pose.bones

    if armature_obj.animation_data is None:
        armature_obj.animation_data_create()

    action = bpy.data.actions.new(action_name)
    action.use_fake_user = True
    armature_obj.animation_data.action = action

    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')

    num_frames = len(bones[0].frames)
    is_player = any(b.parent is None and b.name.lower() == "bip01" for b in armature.bones)
    root_frame = PLAYER_WORLD_FIX @ ROT_FIX if is_player else ROT_FIX

    for frame_idx in range(num_frames):
        for bone_data in bones:
            if bone_data.name not in pose_bones:
                continue

            pose_bone = pose_bones[bone_data.name]
            rot, pos = bone_data.frames[frame_idx]

            engine_local = rot.to_matrix().to_4x4()
            engine_local.translation = pos * scene_scale
            local = BONE_FRAME_INV @ engine_local @ BONE_FRAME

            # Roots have no parent bone; their parent frame is the rig's world frame, not identity.
            rest_bone = pose_bone.bone
            parent_rest = rest_bone.parent.matrix_local if rest_bone.parent else root_frame
            pose_bone.matrix_basis = rest_bone.matrix_local.inverted() @ parent_rest @ local

        for bone_data in bones:
            if bone_data.name not in pose_bones:
                continue
            pb = pose_bones[bone_data.name]
            pb.keyframe_insert("rotation_quaternion", frame=frame_idx)
            pb.keyframe_insert("location", frame=frame_idx)

    bpy.ops.object.mode_set(mode='OBJECT')
    scene = bpy.context.scene
    scene.frame_start = min(scene.frame_start, 0)
    scene.frame_end = max(scene.frame_end, num_frames - 1)


