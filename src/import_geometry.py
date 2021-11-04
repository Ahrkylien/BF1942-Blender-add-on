import bpy

from .standard_mesh import bf42_import_sm
from .tree_mesh import bf42_import_tm
from .misc import *

def bf42_getGeometryTemplateMeshes(geometryTemplate):
    objects = []
    if geometryTemplate.type in ["standardmesh", "animatedmesh", "treemesh"]:
        mesh_path, rel_path = bf42_getMeshPath(geometryTemplate)
        if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
            selected_mesh_collection = bf42_getMeshesCollection()
        elif geometryTemplate.type == "treemesh":
            selected_mesh_collection = bf42_getTreeMeshesCollection()
        meshFound = False
        for blend_collection in selected_mesh_collection.children:
            if revomeBlenderSuffix(blend_collection.name) == rel_path:
                for blend_object in blend_collection.objects:
                    if removesuffix(revomeBlenderSuffix(blend_object.name),["_LOD1","_Branch","_Trunk","_Sprite","_Billboard"]).lower() == rel_path:
                        objects.append(blend_object)
                        meshFound = True
                        if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
                            break
            if meshFound:
                break
    else:
        print("Error: Unknown mesh type: "+geometryTemplate.name+"!!")
    return(objects)

def bf42_importGeometry(geometryTemplate, base_path, level, bf42_data, sceneScale = 1, overwrite = False):
    if geometryTemplate.type in ["standardmesh", "animatedmesh", "treemesh"]:
        if overwrite:
            if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
                selected_mesh_collection = bf42_getMeshesCollection()
            elif geometryTemplate.type == "treemesh":
                selected_mesh_collection = bf42_getTreeMeshesCollection()
            for blend_collection in selected_mesh_collection.children:
                if blend_collection.name == geometryTemplate.name:
                    for object in blend_collection.all_objects:
                        bpy.data.objects.remove(object)
                    bpy.data.collections.remove(blend_collection)
                    break
        objects = bf42_getGeometryTemplateMeshes(geometryTemplate)
        if objects == []:
            print("Object Not Found. Going to Import")
            mesh_path, rel_path = bf42_getMeshPath(geometryTemplate)
            if mesh_path != None:
                if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
                    bf42_import_sm(mesh_path, False, False, True, True, False, True, sceneScale, rel_path)
                elif geometryTemplate.type == "treemesh":
                    bf42_import_tm(mesh_path, False, False, False, True, True, sceneScale, rel_path)
    return(bf42_getGeometryTemplateMeshes(geometryTemplate))