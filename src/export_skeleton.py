from .misc import *


def _sorted_bones(armature):
    """Return bones sorted parent-before-child (required by .ske format)."""
    sorted_bones = []
    visited = set()

    def visit(bone):
        if bone.name in visited:
            return
        if bone.parent:
            visit(bone.parent)
        visited.add(bone.name)
        sorted_bones.append(bone)

    for bone in armature.bones:
        visit(bone)
    return sorted_bones


def export_ske(filepath, armature_obj, scene_scale=1.0):
    armature = armature_obj.data
    bones = _sorted_bones(armature)
    bone_index = {b.name: i for i, b in enumerate(bones)}
    engine_from_armature = (root_turn(b.name for b in armature.bones if b.parent is None) @ ENGINE_TO_BLENDER).inverted().to_4x4()

    absolute = {}
    with open(filepath, 'wb') as f:
        write_uint32(f, 1)
        write_uint32(f, len(bones))
        for bone in bones:
            eng_abs = engine_from_armature @ bone.matrix_local @ BONE_FRAME_INV
            eng_abs.translation /= scene_scale
            absolute[bone.name] = eng_abs
            if bone.parent:
                local = absolute[bone.parent.name].inverted() @ eng_abs
                parent_index = bone_index[bone.parent.name]
            else:
                local = eng_abs
                parent_index = 0xFFFF
            write_string(f, bone.name)
            write_uint16(f, parent_index)
            for row in range(3):
                for col in range(4):
                    write_float(f, local[row][col])
