import os

import bpy
from mathutils import Matrix, Vector

from .misc import *


class Bf1942Bone:
    def __init__(self, name, parent_index, matrix):
        self.name = name
        self.parent_index = parent_index
        # matrix: local-to-parent transform read from .ske.
        # The file stores columns of R_engine, but we read them as rows, giving
        # R_engine^T in Blender's row-major matrix.  Because BF1942 uses row-vector
        # convention (v' = v * M), R_engine^T is the correct column-vector transform
        # for Blender (M @ v).  No further conversion is needed.
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

    def get_absolute_matrix(self):
        if self.parent is None:
            return self.matrix
        return self.parent.get_absolute_matrix() @ self.matrix

    def __repr__(self):
        return f"Bf1942Bone(name={self.name}, parent_index={self.parent_index})"


def read_bones_from_ske(filepath):
    bones = []
    with open(filepath, 'rb') as file:
        header = read_uint32(file)
        if header != 1:
            raise Exception(f"Unsupported .ske version {header}")

        num_bones = read_uint32(file)

        for _ in range(num_bones):
            name_length = read_uint16(file)
            bone_name = read_string(file, name_length)[:-1]  # zero terminated

            parent_index = read_uint16(file)

            # 12 floats: three groups of [col_k_of_R_engine, T_k].
            # Reading as 3 rows of a blender matrix gives R_engine^T, which is
            # the correct column-vector transform matrix for Blender.
            matrix = Matrix([[read_float(file) for _ in range(4)] for _ in range(3)] + [[0, 0, 0, 1]])

            bones.append(Bf1942Bone(bone_name, parent_index, matrix))

    for bone in bones:
        if bone.parent_index != 0xFFFF:
            bone.parent = bones[bone.parent_index]
            bone.parent.children.append(bone)

    return bones


def is_point_on_segment(point, seg_start, seg_end, threshold):
    segment = seg_end - seg_start
    seg_len_sq = segment.dot(segment)
    if seg_len_sq == 0:
        return False
    t = (point - seg_start).dot(segment) / seg_len_sq
    closest = seg_start + t * segment
    return 0.0 <= t <= 1.0 and (point - closest).length < threshold


def get_minimum_distance_between_lines(matrix1, matrix2):
    p1 = matrix1.translation
    p2 = matrix2.translation
    d1 = matrix1.to_3x3() @ Vector((1, 0, 0))
    d2 = matrix2.to_3x3() @ Vector((1, 0, 0))

    cross_d1_d2 = d1.cross(d2)
    if cross_d1_d2.length == 0:
        return None, None, None

    distance = abs((p2 - p1).dot(cross_d1_d2)) / cross_d1_d2.length

    a = d1.dot(d1)
    b = d1.dot(d2)
    c = d2.dot(d2)
    w = p1 - p2
    d = d1.dot(w)
    e = d2.dot(w)

    denominator = a * c - b ** 2
    if denominator != 0:
        t1 = (b * e - c * d) / denominator
        r1 = p1 + t1 * d1
        t2 = (a * e - b * d) / denominator
        r2 = p2 + t2 * d2
        return distance, r1, r2
    return None, None, None


def import_ske(filepath, bone_mode='EXTRAPOLATE', scene_scale=1.0):
    distance_threshold = 0.001 * scene_scale
    extrapolate = bone_mode != 'PURE'
    connect = bone_mode == 'EXTRAPOLATE_CONNECT'

    bones = read_bones_from_ske(filepath)
    for bone in bones:
        for row in range(3):
            bone.matrix[row][3] *= scene_scale

    to_blender = root_turn(bone.name for bone in bones if bone.is_root) @ ENGINE_TO_BLENDER

    object_name = os.path.splitext(bpy.path.basename(filepath))[0]

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.armature_add(location=(0.0, 0.0, 0.0))
    armature = bpy.context.object
    armature.name = object_name
    bpy.context.view_layer.objects.active = armature

    bpy.ops.object.mode_set(mode='EDIT')
    armature.data.edit_bones.remove(armature.data.edit_bones[0])

    for bone in bones:
        bone.blender_bone = armature.data.edit_bones.new(bone.name)

    for bone in bones:
        eb = bone.blender_bone
        mtr = bone.get_absolute_matrix()

        if bone.parent is not None:
            eb.parent = bone.parent.blender_bone

        eb.head = to_blender @ mtr.translation
        eb.tail = to_blender @ (mtr @ Vector((0.03 * scene_scale, 0, 0)))

        if connect and not bone.is_root:
            parent_eb = bone.parent.blender_bone
            if is_point_on_segment(to_blender @ mtr.translation, parent_eb.head, parent_eb.tail, distance_threshold):
                eb.use_connect = True

        if extrapolate and not bone.is_leaf_bone:
            minimum_distance, pos1, pos2 = get_minimum_distance_between_lines(bone.children[0].get_absolute_matrix(), mtr)
            if minimum_distance is not None and minimum_distance < distance_threshold:
                eb.tail = to_blender @ pos1

        eb.align_roll(to_blender @ mtr.to_3x3().col[1])

    bpy.ops.object.mode_set(mode='OBJECT')
    armature.data.display_type = 'OCTAHEDRAL'
    return armature
