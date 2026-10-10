import struct
import math
from mathutils import Matrix

ROT_FIX = Matrix.Rotation(-math.pi / 2, 4, 'Z')
ROT_FIX_INV = ROT_FIX.inverted()


def _write_float(file, v):  file.write(struct.pack('<f', v))
def _write_uint16(file, v): file.write(struct.pack('<H', v))
def _write_uint32(file, v): file.write(struct.pack('<I', v))

def _write_string(file, s):
    encoded = s.encode('ascii') + b'\x00'  # nameLen includes NUL
    _write_uint16(file, len(encoded))
    file.write(encoded)

def _engine_matrix(bone, scene_scale=1.0):
    """Local-to-parent matrix in engine space for a rest-pose bone."""
    # bone.matrix_local ≈ mtr_engine_abs @ ROT_FIX, so mtr_engine_abs ≈ bone.matrix_local @ ROT_FIX_INV
    eng_abs = bone.matrix_local @ ROT_FIX_INV
    eng_abs.translation /= scene_scale
    if bone.parent:
        parent_eng_abs = bone.parent.matrix_local @ ROT_FIX_INV
        parent_eng_abs.translation /= scene_scale
        return parent_eng_abs.inverted() @ eng_abs
    return eng_abs

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

    with open(filepath, 'wb') as f:
        _write_uint32(f, 1)  # version
        _write_uint32(f, len(bones))

        for bone in bones:
            _write_string(f, bone.name)

            parent_idx = bone_index[bone.parent.name] if bone.parent else 0xFFFF
            _write_uint16(f, parent_idx)

            # Write first 3 rows of the engine local-to-parent matrix (12 floats).
            # This is the inverse of how we read: rows of the Blender matrix map to
            # the column-major layout the engine expects.
            mtr = _engine_matrix(bone, scene_scale)
            for row in range(3):
                for col in range(4):
                    _write_float(f, mtr[row][col])
