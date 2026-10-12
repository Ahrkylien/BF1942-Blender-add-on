from mathutils import Vector, kdtree

from .misc import *

REST_SHAPE = "BF1942 rest"


def parse_skn(filepath):
    """
    Return (vertex_positions, vertex_weights, bone_names).

    vertex_positions : list of (x, y, z) in engine space
    vertex_weights   : list of lists of (bone_idx, weight, rel_x, rel_y, rel_z)
    bone_names       : list of str
    """
    vertex_positions = []
    vertex_weights = []
    with open(filepath, 'rb') as f:
        header = read_uint32(f)
        if header != 1:
            raise Exception(f"Unsupported .skn version {header}")

        num_vertices = read_uint32(f)
        for _ in range(num_vertices):
            x, y, z = read_float(f), read_float(f), read_float(f)
            vertex_positions.append((x, y, z))
            num_w = read_uint8(f)
            vw = []
            for _ in range(num_w):
                bone_idx = read_uint16(f)
                w = read_float(f)
                rx, ry, rz = read_float(f), read_float(f), read_float(f)
                vw.append((bone_idx, w, rx, ry, rz))
            vertex_weights.append(vw)

        num_bones = read_uint16(f)
        bone_names = []
        for _ in range(num_bones):
            name_len = read_uint16(f)
            bone_names.append(read_string(f, name_len)[:-1])  # zero-terminated

    return vertex_positions, vertex_weights, bone_names


def apply_skin(mesh_obj, armature_obj, vertex_positions, vertex_weights, bone_names, scene_scale=1.0):
    """
    Bind the mesh to the armature and fold it onto the armature's rest pose.

    The skin data gives each vertex's position in its bones' local frames. Summing the
    weighted rest transforms of those positions gives the vertex's rest position, stored
    in a shape key. The bind geometry stays in the basis and the bones are not moved.
    Returns (matched, total) mesh vertex counts.
    """
    mesh = mesh_obj.data
    total = len(mesh.vertices)

    if mesh.shape_keys:
        mesh_obj.active_shape_key_index = 0
        if REST_SHAPE in mesh.shape_keys.key_blocks:
            mesh_obj.shape_key_remove(mesh.shape_keys.key_blocks[REST_SHAPE])
    else:
        mesh_obj.shape_key_add(name="Basis", from_mix=False)

    for name in bone_names:
        existing = mesh_obj.vertex_groups.get(name)
        if existing is not None:
            mesh_obj.vertex_groups.remove(existing)
        mesh_obj.vertex_groups.new(name=name)

    tree = kdtree.KDTree(len(vertex_positions))
    for i, p in enumerate(vertex_positions):
        tree.insert((ENGINE_TO_BLENDER @ Vector(p)) * scene_scale, i)
    tree.balance()

    rest_of_bone = {}
    for name in bone_names:
        bone = armature_obj.data.bones.get(name)
        if bone is not None:
            rest_of_bone[name] = armature_obj.matrix_world @ bone.matrix_local

    tolerance = 1e-3 * scene_scale
    inverse_matrix = mesh_obj.matrix_world.inverted()
    rest_coords = []
    matched = 0
    for v in mesh.vertices:
        rest_co = v.co.copy()
        _, skn_index, distance = tree.find(mesh_obj.matrix_world @ v.co)
        if distance <= tolerance:
            matched += 1
            groups = {}
            rest_world = Vector((0.0, 0.0, 0.0))
            weight_sum = 0.0
            for bone_idx, w, rx, ry, rz in vertex_weights[skn_index]:
                if bone_idx >= len(bone_names) or w <= 0.0:
                    continue
                name = bone_names[bone_idx]
                groups[name] = groups.get(name, 0.0) + w
                if name in rest_of_bone:
                    rel = Vector((rx, ry, rz)) * scene_scale
                    rest_world += (rest_of_bone[name] @ (BONE_FRAME_INV @ rel)) * w
                    weight_sum += w
            for name, w in groups.items():
                mesh_obj.vertex_groups[name].add([v.index], w, 'REPLACE')
            if weight_sum > 0.0:
                rest_co = inverse_matrix @ (rest_world / weight_sum)
        rest_coords.append(rest_co)

    rest = mesh_obj.shape_key_add(name=REST_SHAPE, from_mix=False)
    for vi, co in enumerate(rest_coords):
        rest.data[vi].co = co
    rest.value = 1.0
    mesh_obj.active_shape_key_index = 0

    modifier = next((m for m in mesh_obj.modifiers if m.type == 'ARMATURE' and m.object == armature_obj), None)
    if modifier is None:
        modifier = mesh_obj.modifiers.new("Armature", 'ARMATURE')
        modifier.object = armature_obj
    modifier.use_bone_envelopes = False
    modifier.use_vertex_groups = True
    return matched, total
