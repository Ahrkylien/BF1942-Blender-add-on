from .misc import *


def export_skn(filepath, mesh_obj, armature_obj, scene_scale=1.0):
    mesh = mesh_obj.data
    armature = armature_obj.data
    keys = mesh.shape_keys
    bind = keys.reference_key.data if keys else mesh.vertices
    rest = keys.key_blocks[REST_SHAPE].data if keys and REST_SHAPE in keys.key_blocks else bind

    bone_rest = {b.name: armature_obj.matrix_world @ b.matrix_local for b in armature.bones}
    bone_order = {b.name: i for i, b in enumerate(armature.bones)}
    group_names = {g.index: g.name for g in mesh_obj.vertex_groups}

    influences = [
        [(group_names[g.group], g.weight) for g in v.groups
         if g.weight > 0.0 and group_names[g.group] in bone_rest]
        for v in mesh.vertices
    ]
    used = sorted({name for infl in influences for name, _ in infl}, key=bone_order.get)
    used_index = {name: i for i, name in enumerate(used)}
    rest_inverse = {name: bone_rest[name].inverted() for name in used}
    engine_from_blender = ENGINE_TO_BLENDER.inverted()

    with open(filepath, 'wb') as f:
        write_uint32(f, 1)
        write_uint32(f, len(mesh.vertices))
        for i in range(len(mesh.vertices)):
            bind_engine = (engine_from_blender @ (mesh_obj.matrix_world @ bind[i].co)) / scene_scale
            write_float(f, bind_engine.x)
            write_float(f, bind_engine.y)
            write_float(f, bind_engine.z)

            rest_world = mesh_obj.matrix_world @ rest[i].co
            write_uint8(f, len(influences[i]))
            for name, weight in influences[i]:
                local = (BONE_FRAME @ (rest_inverse[name] @ rest_world)) / scene_scale
                write_uint16(f, used_index[name])
                write_float(f, weight)
                write_float(f, local.x)
                write_float(f, local.y)
                write_float(f, local.z)

        write_uint16(f, len(used))
        for name in used:
            write_string(f, name)
