import os
import struct
import bpy
import math
from mathutils import Matrix, Vector

# Helper function to read a float (4 bytes) from the file
def read_float(file):
    return struct.unpack('<f', file.read(4))[0]

# Helper function to read a uint16 (2 bytes) from the file
def read_uint16(file):
    return struct.unpack('<H', file.read(2))[0]

# Helper function to read a uint32 (4 bytes) from the file
def read_uint32(file):
    return struct.unpack('<I', file.read(4))[0]

# Helper function to read a char[] as a string from the file
def read_string(file, length):
    return file.read(length).decode('utf-8')

def convert_right_to_left_handed_matrix(M: Matrix) -> Matrix:
    """Converts a 4x4 transformation matrix from right to left handed coordinate system by swapping Y and Z axes."""
    return Matrix([
        [M[0][0], M[0][2], M[0][1], M[0][3]],
        [M[2][0], M[2][2], M[2][1], M[2][3]],
        [M[1][0], M[1][2], M[1][1], M[1][3]],
        [M[3][0], M[3][2], M[3][1], M[3][3]],
    ])

def convert_to_blender_matrix(M: Matrix) -> Matrix:
    """Converts a 4x4 transformation matrix to Blender's coordinate system by swapping Y and Z axes."""
    return Matrix([
        [-M[0][0], -M[0][1], -M[0][2], -M[0][3]],
        [-M[1][0], -M[1][1], -M[1][2], -M[1][3]],
        [-M[2][0], -M[2][1], -M[2][2], -M[2][3]],
        [-M[3][0], M[3][1], M[3][2], M[3][3]],
    ])

transformation_matrix = Matrix([
    [-1, 0, 0, 0],
    [0, -1, 0, 0],
    [0, 0, -1, 0],
    [0, 0, 0, 1]
])

def convert_from_right_to_left_coordinate_system(obj):
    bpy.ops.object.mode_set(mode='EDIT')
    obj.data.transform(transformation_matrix)
    bpy.ops.object.mode_set(mode='OBJECT')

class Bf1942Bone:
    def __init__(self, name, parent_index, matrix):
        self.name = name
        self.parent_index = parent_index
        self.matrix = matrix
        self.parent = None
        self.children = []
        
        self.blender_bone = None
        
    @property
    def is_root(self):
        return self.parent is None
        
    @property
    def is_leaf_bone(self):
        return self.children == []
        
    @property
    def is_intermediate_bone(self):
        return not self.is_root and not self.is_leaf_bone
        
    @property
    def absolute_position(self):
        matrix = self.get_absolute_matrix()
        return Vector((matrix[0][3], matrix[1][3], matrix[2][3]))
        
    def get_absolute_position(self):
        matrix = self.get_absolute_matrix()
        return (matrix[0][3], matrix[1][3], matrix[2][3])
        
    def get_absolute_position2(self):
        relative_vector = self.get_relative_position()
        matrix = self.get_ansestors_matrix()
        return matrix @ relative_vector
        
    def get_absolute_matrix(self):
        return self.parent.get_absolute_matrix() @ self.matrix if self.parent != None else self.matrix
        
    def get_ansestors_matrix(self):
        return self.parent.get_absolute_matrix() if self.parent != None else Matrix.Identity(4)
        
    def get_relative_position(self):
        return Vector([self.matrix[0][3], self.matrix[1][3], self.matrix[2][3]])

    def __repr__(self):
        return f"Bf1942Bone(name={self.name}, parent_index={self.parent_index}:\n{self.matrix})"

# Function to load and parse the .ske file
def read_bones_from_ske(filepath):
    # Create a list to hold the bones
    bones = []
        
    # Open the .ske file
    with open(filepath, 'rb') as file:
        # Read header and verify version
        header = read_uint32(file)
        if header != 1:
            raise Exception(f"Unsupported .ske version {header}")

        # Read number of bones
        num_bones = read_uint32(file)
        print(f"Number of bones: {num_bones}")

        # Iterate through each bone
        for i in range(num_bones):
            # Read bone name length and name
            name_length = read_uint16(file)
            bone_name = read_string(file, name_length)[:-1] # zero terminated
            
            # Read parent index (FFFF or FFFE indicates no parent)
            parent_index = read_uint16(file)

            # Read transformation matrix
            matrix = Matrix([[read_float(file) for _ in range(4)] for _ in range(3)] + [[0, 0, 0, 1]])
            
            bones.append(Bf1942Bone(bone_name, parent_index, matrix))
    
    for bone in bones:
        if bone.parent_index != 0xFFFF:
            bone.parent = bones[bone.parent_index]
            bone.parent.children.append(bone)

    return bones

def get_minimum_distance_between_lines_v1(matrix1, matrix2):
    # Extract origins (position)
    p1 = matrix1.translation
    p2 = matrix2.translation

    # Extract directions (Z-axis of each matrix)
    d1 = matrix1.to_3x3() @ Vector((0.01, 0, 0))
    d2 = matrix2.to_3x3() @ Vector((0.01, 0, 0))

    # Compute the cross product of direction vectors
    cross_d1_d2 = d1.cross(d2)

    # Check if lines are parallel
    if cross_d1_d2.length == 0:
        return None

    # Compute the minimal distance formula
    return abs((p2 - p1).dot(cross_d1_d2)) / cross_d1_d2.length

def get_minimum_distance_between_lines(matrix1, matrix2):
    # Extract origins (position)
    p1 = matrix1.translation
    p2 = matrix2.translation

    # Extract directions (use the X-axis for direction as an example)
    d1 = matrix1.to_3x3() @ Vector((1, 0, 0))  # Using X-axis for direction
    d2 = matrix2.to_3x3() @ Vector((1, 0, 0))  # Using X-axis for direction

    # Compute the cross product of direction vectors
    cross_d1_d2 = d1.cross(d2)

    # Check if lines are parallel
    if cross_d1_d2.length == 0:
        return None, None, None  # Lines are parallel, return None for coordinates and distance

    # Compute the minimum distance
    distance = abs((p2 - p1).dot(cross_d1_d2)) / cross_d1_d2.length

    # Calculate the closest point on the first line (r1)
    a = (d1.dot(d1))
    b = d1.dot(d2)
    c = d2.dot(d2)
    w = p1 - p2
    d = d1.dot(w)
    e = d2.dot(w)
    
    denominator = (a * c - b ** 2)
    if denominator != 0:
        t1 = (b * e - c * d) / denominator
        r1 = p1 + (t1 * d1)  # Closest point on the first line

        # Closest point on the second line (r2)
        t2 = (a * e - b * d) / denominator
        r2 = p2 + (t2 * d2)  # Closest point on the second line

        return distance, r1, r2
    else:
        # If lines are parallel, return None for coordinates
        return None, None, None

def import_ske(filepath):
    distance_threshold = 0.001;
    
    bones = read_bones_from_ske(filepath)
    
    object_name = os.path.splitext(bpy.path.basename(filepath))[0]
    
    if (bpy.context.mode != 'OBJECT'):
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.armature_add()
    armature = bpy.context.object
    armature.name = object_name
    bpy.context.view_layer.objects.active = armature

    bpy.ops.object.mode_set(mode='EDIT')
    
    # remove the default bone
    armature.data.edit_bones.remove(armature.data.edit_bones[0])

    for bone in bones:
        bone.blender_bone = bpy.context.active_object.data.edit_bones.new(bone.name)
        
    for bone in bones:
        blender_bone = bone.blender_bone
        
        if bone.parent != None:
            blender_bone.parent = bone.parent.blender_bone;
        
        if bone.is_root:
            pass
        
        mtr = bone.get_absolute_matrix()
        blender_bone.head = mtr@ Vector((-0.03, 0, 0))
        blender_bone.tail = mtr@ Vector((0.03, 0, 0))
        
        if not bone.is_root:
            minimum_distance, pos1, pos2 = get_minimum_distance_between_lines(bone.parent.get_absolute_matrix(), mtr)
            if minimum_distance is not None and minimum_distance < distance_threshold:
                blender_bone.use_connect = True
            elif not bone.is_leaf_bone: # this is a prediction for intermediate bones and not perse correct (make it a setting)
                blender_bone.head = bone.absolute_position
        
        if not bone.is_leaf_bone:
            minimum_distance, pos1, pos2 = get_minimum_distance_between_lines(bone.children[0].get_absolute_matrix(), mtr)
            if minimum_distance is not None and minimum_distance < distance_threshold:
                blender_bone.tail = pos1
        
        # root bone is not realy connected. just for general rotations?
        # middle bone with 1 child: then pos is start of bone, and en is probably the next pos
        # middle bone with n childs: hen pos is start of bone, and en is somewhere
        # if last then pos is the middle. start is where previous and this meet, end is ..?
        
        
        
        # head is where the parent cuts off the bone
        # if no parent or cut then go default
        
        # tail is where all children cut off bone
        # if no children or not all children cut off bone at same place go default
        
        # if resulting length is 0 go default for both
        
        # if head is not default set connected
        # connected means when the bones head start from the parents tail
        
        # need to keep track of where the center of the bone is?? idk depends on how skn and baf work
        # this is for later
        
        
        #else:
          #  blender_bone.length = 0.03
        
        # Set the bone's head (position) from the matrix translation
        #translation = bone.get_absolute_position2()
        #bone.blender_bone.head = (translation[0] + 0.1, translation[1], translation[2])
        
        # Set the bone's tail (position, for visualization)
        #bone.blender_bone.tail = (translation[0] - 0.1, translation[1], translation[2])
        
        #bone.blender_bone.matrix =  test2 @ bone.get_absolute_matrix() @ test
        
    bpy.ops.object.mode_set(mode='OBJECT')
    armature.data.display_type = 'STICK'
    
    #convert_from_right_to_left_coordinate_system(armature)

test2 = Matrix([
    [-1, 0, 0, 0],
    [0, 0, -1, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1]
])


test = Matrix([
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 1]
])

# Example usage
# Replace the path below with your .ske file's path
import_ske(r"D:\MOD\Battlefield 1942 extracted (orid)\animations\UsSoldier.ske")
