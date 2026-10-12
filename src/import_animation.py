import bpy
from mathutils import Quaternion, Vector

from .misc import *


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


class BafBone:
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
            bones.append(BafBone(name))

        num_frames = read_uint32(file)
        precision = read_uint8(file)

        for bone in bones:
            read_uint16(file)  # num_data (unused)
            bone_channels = [[] for _ in range(7)]  # channels: x,y,z,w rot + x,y,z pos

            for i in range(7):
                bits = 15 if i <= 3 else precision
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
                        bone_channels[i].extend([read_16bit_fixed_point_float(file, bits)] * num_frames_in_block)
                    else:
                        bone_channels[i].extend(read_16bit_fixed_point_float(file, bits) for _ in range(num_frames_in_block))

                if total_frames != num_frames:
                    raise Exception(
                        f"Bone '{bone.name}' channel {i} has {total_frames} frames, expected {num_frames}"
                    )

            # Channels: [qx, qy, qz, qw, tx, ty, tz] in engine space.
            # The stored quaternion uses row-vector convention, so its conjugate is the column-vector rotation.
            for qx, qy, qz, qw, tx, ty, tz in zip(*bone_channels):
                bone.frames.append((Quaternion((qw, -qx, -qy, -qz)), Vector((tx, ty, tz))))

        data_left = tell_remaining_length(file)
        if data_left != 0:
            raise Exception(f"{data_left} unexpected bytes remaining at end of file")

    return bones


def apply_animation(armature_obj, bones, action_name="BF1942Anim", scene_scale=1.0):
    """Apply parsed .baf animation to an armature object. Returns the names of animated bones the armature lacks."""
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
    skipped = [bone.name for bone in bones if bone.name not in pose_bones]
    tracked = [bone for bone in bones if bone.name in pose_bones]
    root_frame = root_turn(b.name for b in armature.bones if b.parent is None).to_4x4() @ ROT_FIX

    for frame_idx in range(num_frames):
        for bone_data in tracked:
            pose_bone = pose_bones[bone_data.name]
            rot, pos = bone_data.frames[frame_idx]

            engine_local = rot.to_matrix().to_4x4()
            engine_local.translation = pos * scene_scale
            local = BONE_FRAME_INV @ engine_local @ BONE_FRAME

            # Roots have no parent bone; their parent frame is the rig's world frame, not identity.
            rest_bone = pose_bone.bone
            parent_rest = rest_bone.parent.matrix_local if rest_bone.parent else root_frame
            pose_bone.matrix_basis = rest_bone.matrix_local.inverted() @ parent_rest @ local
            pose_bone.keyframe_insert("rotation_quaternion", frame=frame_idx)
            pose_bone.keyframe_insert("location", frame=frame_idx)

    bpy.ops.object.mode_set(mode='OBJECT')
    scene = bpy.context.scene
    scene.frame_start = min(scene.frame_start, 0)
    scene.frame_end = max(scene.frame_end, num_frames - 1)
    return skipped
