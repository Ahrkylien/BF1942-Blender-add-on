import bpy
import struct
import math
from mathutils import Quaternion, Vector, Matrix

# Must match the ROT_FIX used in import_skeleton.py
ROT_FIX = Matrix.Rotation(-math.pi / 2, 4, 'Z')
ROT_FIX_INV = ROT_FIX.inverted()

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
        print(f"num_bones: {num_bones}, num_frames: {num_frames}, precision: {precision}")

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

            # Channels: [qx, qy, qz, qw, tx, ty, tz]
            # BF1942 uses row-vector convention (v' = v * M), so the stored quaternion q
            # represents R_q in engine terms.  In Blender's column-vector convention the
            # same rotation is R_q^T = R_{conjugate(q)}, so we negate the xyz components.
            for qx, qy, qz, qw, tx, ty, tz in zip(*bone_channels):
                rot = Quaternion((qw, -qx, -qy, -qz))  # conjugate for column-vector convention
                pos = Vector((tx, ty, tz))              # Z-up matches Blender, no swap needed
                bone.frames.append((rot, pos))

        data_left = tell_remaining_length(file)
        if data_left != 0:
            raise Exception(f"{data_left} unexpected bytes remaining at end of file")

    return bones


def apply_animation(armature_obj, bones, action_name="BF1942Anim"):
    """Apply parsed .baf animation to an armature object."""
    armature = armature_obj.data
    pose_bones = armature_obj.pose.bones
    rest_bones = armature.bones

    # Strip ROT_FIX from each bone's rest matrix so we get the raw engine-space
    # absolute matrix.  The animation data is in that same engine space.
    rest_matrix = {b.name: b.matrix_local @ ROT_FIX_INV for b in rest_bones}

    if armature_obj.animation_data is None:
        armature_obj.animation_data_create()

    action = bpy.data.actions.new(action_name)
    armature_obj.animation_data.action = action

    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')

    num_frames = len(bones[0].frames)

    for frame_idx in range(num_frames):
        for bone_data in bones:
            if bone_data.name not in pose_bones:
                continue

            pose_bone = pose_bones[bone_data.name]
            rot, pos = bone_data.frames[frame_idx]

            # Build local-to-parent matrix from animation data
            anim_local = rot.to_matrix().to_4x4()
            anim_local.translation = pos

            # Append ROT_FIX so the animated frame matches the fixed bone orientation.
            # Use the engine-space parent rest matrix (ROT_FIX already stripped above).
            if pose_bone.bone.parent and pose_bone.bone.parent.name in rest_matrix:
                arm_matrix = rest_matrix[pose_bone.bone.parent.name] @ anim_local @ ROT_FIX
            else:
                arm_matrix = anim_local @ ROT_FIX

            pose_bone.matrix_basis = pose_bone.bone.matrix_local.inverted() @ arm_matrix

        for bone_data in bones:
            if bone_data.name not in pose_bones:
                continue
            pb = pose_bones[bone_data.name]
            pb.keyframe_insert("rotation_quaternion", frame=frame_idx)
            pb.keyframe_insert("location", frame=frame_idx)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = num_frames - 1
    print(f"Applied {num_frames} frames to '{armature_obj.name}'")


# ---------------------------------------------------------------------------
# Test entry point — edit paths and armature name as needed
# ---------------------------------------------------------------------------

BAF_FILE  = r"D:\MOD\Battlefield 1942 extracted (orid)\animations\StandWalkRun\LowerBody\3PJumpStandLower.baf"
ARMATURE_NAME = "UsSoldier"

bones = parse_baf(BAF_FILE)

armature = bpy.data.objects.get(ARMATURE_NAME)
if not armature:
    raise Exception(f"Armature '{ARMATURE_NAME}' not found in scene")

import os
action_name = os.path.splitext(os.path.basename(BAF_FILE))[0]
apply_animation(armature, bones, action_name)
