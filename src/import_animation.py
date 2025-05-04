import bpy
import struct
from collections import namedtuple
from mathutils import Quaternion, Vector, Matrix, Euler
import math

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

def read_half_float(file):
    """Read 2 bytes and unpack as float16"""
    return struct.unpack('<e', file.read(2))[0]

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
    file.seek(0, 2)  # Seek to end of file
    end_pos = file.tell()
    file.seek(current_pos)  # Go back to where you were
    return end_pos - current_pos


def get_local_matrix(bone):
    return bone.matrix if bone.parent is None else bone.parent.matrix.inverted() @ bone.matrix

class Bf1942Bone:
    def __init__(self, name):
        self.name = name
        self.frames = []


def parse_baf(filepath):
    bones = []
    with open(filepath, 'rb') as file:
        # Read header and verify version
        header = read_uint32(file)
        if header != 3:
            raise Exception(f"Unsupported .baf version {header}")
        
        # Bone names
        num_bones = read_uint16(file)
        for _ in range(num_bones):
            name_len = read_uint16(file)
            name = read_string(file, name_len)[:-1] # zero terminated
            bones.append(Bf1942Bone(name))
            print(f"name: {name}")

        # Frame and precision
        num_frames = read_uint32(file)
        precision = read_uint8(file)
        print(f"num_frames: {num_frames}")
        print(f"precision: {precision}")

        for bone_index in range(num_bones):
            bone = bones[bone_index]
            num_data = read_uint16(file)

            bone_frames = [[] for _ in range(7)]  # 4 rotation + 3 position

            for i in range(7):
                block_data_size = read_uint16(file)  # excluding the first two bytes of the sub-blocks
                data_left_to_read = block_data_size
                
                total_number_of_frames_in_bone = 0

                while data_left_to_read > 0:
                    tmp = read_uint8(file)
                    num_frames_in_block = tmp & 0b01111111
                    is_rle = (tmp >> 7) == 1
                    sub_block_data_size = read_uint8(file)
                    total_number_of_frames_in_bone += num_frames_in_block
                    data_left_to_read -= sub_block_data_size

                    if is_rle:
                        val = read_16bit_fixed_point_float(file, 15 if i <= 3 else precision)
                        bone_frames[i].extend([val] * num_frames_in_block)
                    else:
                        for _ in range(num_frames_in_block):
                            val = read_16bit_fixed_point_float(file, 15 if i <= 3 else precision)
                            bone_frames[i].append(val)
                
                if total_number_of_frames_in_bone != num_frames:
                    raise Exception(f"Bone {bone.name} has {total_number_of_frames_in_bone} frames instead of {num_frames} for float {i}")
            
            # Zip 7 separate lists into per-frame data
            for frame_values in zip(*bone_frames):
                rot = Quaternion([frame_values[3], frame_values[0], frame_values[1], frame_values[2]])  # blenders Quaternion starts with 'w'
                pos = Vector(frame_values[4:7])
                bone.frames.append((rot, pos))
            
        data_left = tell_remaining_length(file)
        if data_left != 0:
            raise Exception(f"There are {data_left} unexpected bytes remaining at the end of the file")
        

    return bones



bones = parse_baf(r"D:\MOD\Battlefield 1942 extracted (orid)\animations\StandWalkRun\LowerBody\3PJumpStandLower.baf")


base = 'UsSoldier'
#base = 'UsSoldierUnConnected'


armature = bpy.data.objects.get(base)

if not armature:
    raise Exception("Armature 'UsSoldier' not found")

# Duplicate the armature
armature_copy = armature.copy()
armature_copy.data = armature.data.copy()  # Duplicate the armature's data
bpy.context.collection.objects.link(armature_copy)  # Link to current collection

# Set the new armature to be the active object
bpy.context.view_layer.objects.active = armature_copy
armature_copy.select_set(True)

# Go to Pose mode to manipulate bones
bpy.ops.object.mode_set(mode='POSE')

pose_bones = armature_copy.pose.bones

for frame_number in range(0, len(bones[0].frames)):
    #cheat for now:
    pose_bones_matrix = {}

    # Now iterate over the bones and apply the position and rotation from your parsed data
    for bone in bones:
        # Look up the bone by name in the duplicated armature
        if not bone.name in armature_copy.pose.bones:
            print(f"Bone '{bone.name}' not found {bone.frames[0][1]}")
            continue
        if False and bone.name != "Bip01":
            continue
        if False and bone.name == "Bip01 L Calf":
            break
        if False and bone.name not in ["Bip01", "Spine Root", "Bip01 Pelvis", "Bip01 L Thigh"]:
            continue
        
        
        pose_bone = pose_bones[bone.name]
        
        # reset frame pose (previous frame pose is current state):
        pose_bone.location = (0 ,0, 0)
        pose_bone.rotation_quaternion = (1, 0, 0, 0)
        
        # bring to 0,0,0
        if base == "UsSoldierUnConnected":
            current_absolute_rotation = pose_bone.matrix.to_quaternion()
            if pose_bone.parent is not None:
                current_location = - (current_absolute_rotation.inverted() @ (pose_bone.parent.head - pose_bone.head))
                parent_absolute_rotation = pose_bone.parent.matrix.to_quaternion()
                current_rotation = parent_absolute_rotation.rotation_difference(current_absolute_rotation)
            else:
                current_location = - (current_absolute_rotation.inverted() @ (-pose_bone.head))
                current_rotation = current_absolute_rotation
            pose_bone.location = -current_location
            pose_bone.rotation_quaternion = current_rotation.inverted()
        
            # rotate from y to x
            #rotation_y_to_x = Quaternion((0, 0, 1), math.radians(-90))
            #pose_bone.rotation_quaternion = rotation_y_to_x @ pose_bone.rotation_quaternion

        # Get the position and rotation (assuming: frame = (rotation, position))
        rot, pos = bone.frames[frame_number]
        
        rot = Quaternion([-rot.w, rot.x, rot.y, rot.z])
        pos = Vector([pos.x, pos.y, pos.z])
        
        #rot.rotate(Euler((0, 1.5708, 0), 'XYZ'))
        #if pose_bone.parent is not None:
        #    pos.rotate(Euler((0, -1.5708, 0), 'XYZ'))

        transformation_matrix_frame = rot.to_matrix().to_4x4()
        transformation_matrix_frame.translation = pos
        
        
        #transformation_matrix_frame.translation = Vector([local[0][3], local[1][3], local[2][3]])
        """
        transformation_matrix_frame = Matrix.Translation([pos[0], pos[1], pos[2]])
        transformation_matrix_frame = get_local_matrix(pose_bone)
        transformation_matrix_frame[0][3] = pos[0]
        transformation_matrix_frame[1][3] = pos[1]
        transformation_matrix_frame[2][3] = pos[2]
        """
        
        
        mode = 1
        
        #parent_matrix
        if mode == 1:
            pose_bone.location += pos
            pose_bone.rotation_quaternion @= rot
            #pose_bone.rotation_quaternion = rot @ pose_bone.rotation_quaternion
        elif mode == 2:
            if pose_bone.parent is not None:
                parent = pose_bone.parent
                parent_matrix = pose_bones_matrix[parent.name]
                parent_rotation = parent_matrix.to_quaternion()
                new_absolute_transformation_matrix = parent_matrix @ transformation_matrix_frame
            else:
                new_absolute_transformation_matrix = transformation_matrix_frame
            pose_bone.matrix_basis = transformation_matrix_frame
            pose_bones_matrix[bone.name] = new_absolute_transformation_matrix
        elif mode == 3:
            if pose_bone.parent is not None:
                parent = pose_bone.parent
                parent_matrix = pose_bones_matrix[parent.name]
                parent_rotation = parent_matrix.to_quaternion()
                new_absolute_transformation_matrix = parent_matrix @ transformation_matrix_frame
                pose_bone.location = parent_rotation @ pos # without rot this worked
            else:
                new_absolute_transformation_matrix = transformation_matrix_frame
                pose_bone.location = pos # without rot this worked
            pose_bones_matrix[bone.name] = new_absolute_transformation_matrix
            
        elif pose_bone.parent is not None:
            """
            mid_point = parent.head
            direction = (parent.tail - mid_point).normalized()
            x_axis = Vector((1, 0, 0))
            quat = x_axis.rotation_difference(direction)
            rot_matrix = quat.to_matrix().to_4x4()
            trans_matrix = Matrix.Translation(mid_point)
            parent_matrix = trans_matrix @ rot_matrix
            """
            
            print(f"{bone.name}:\n{rot}\n{pos}\n{transformation_matrix_frame}\n{parent_matrix}")
            # pose_bone.location = parent_rotation @ pos # without rot this worked
            #pose_bone.location = pos
            #pose_bone.rotation_quaternion = rot
            pose_bone.matrix_basis = transformation_matrix_frame
            #pose_bone.tail = new_absolute_transformation_matrix @ Vector((0.08, 0, 0))
            pose_bones_matrix[bone.name] = new_absolute_transformation_matrix
        else:
            
            print(f"{bone.name}:\n{rot}\n{pos}\n{transformation_matrix_frame}")
            pose_bone.matrix_basis = transformation_matrix_frame
            #pose_bone.tail = new_absolute_transformation_matrix @ Vector((0.08, 0, 0))
            pose_bones_matrix[bone.name] = transformation_matrix_frame
        
        #pose_bone.matrix = new_absolute_transformation_matrix
        #pose_bone.rotation_quaternion = rot

        # Apply the position (set the bone's head to the position)
        #pose_bone.location = pos  # This sets the position in local space (relative to parent)

        #pose_bone.rotation_quaternion = rot  # Set quaternion rotation directly


    # fix rotations:
    if base != "UsSoldierUnConnected":
        for bone in pose_bones:
            if bone.parent:
                rotation = Quaternion((0, 0, 1), math.radians(90))
                bone.location = rotation @ bone.location
                bone.rotation_quaternion = rotation @ bone.rotation_quaternion
            local_z_axis = bone.rotation_quaternion @ Vector((0, 0, 1))
            rotation = Quaternion(local_z_axis, math.radians(-90))
            bone.rotation_quaternion = rotation @ bone.rotation_quaternion

    for bone in pose_bones:
        bone.keyframe_insert("rotation_quaternion", frame=frame_number)
        bone.keyframe_insert("location", frame=frame_number)


bpy.context.view_layer.update()
# Return to Object Mode after editing
bpy.ops.object.mode_set(mode='OBJECT')
