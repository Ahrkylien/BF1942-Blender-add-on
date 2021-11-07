import bpy

from .standard_mesh import bf42_import_sm
from .tree_mesh import bf42_import_tm
from .misc import *

def bf42_getGeometryTemplateMeshes(geometryTemplate):
    objects = []
    if geometryTemplate.type in ["standardmesh", "animatedmesh", "treemesh"]:
        mesh_path, rel_path = bf42_getMeshPath(geometryTemplate)
        if mesh_path == None:
            return([])
        if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
            meshCollection = bf42_getMeshesCollection()
        elif geometryTemplate.type == "treemesh":
            meshCollection = bf42_getTreeMeshesCollection()
        
        # find collection:
        meshPath = rel_path.split("/")
        fileName = meshPath.pop()
        for dir in meshPath:
            meshCollection = bf42_getCollectionByName(dir,meshCollection, False)
            if meshCollection == None:
                return([])
        meshCollection = bf42_getCollectionByName(fileName,meshCollection, False)
        if meshCollection == None:
            return([])
        
        for blend_object in meshCollection.objects:
            if removesuffix(revomeBlenderSuffix(blend_object.name),["_LOD1","_Branch","_Trunk","_Sprite","_Billboard"]).lower() == fileName.lower():
                objects.append(blend_object)
                if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
                    break
    else:
        print("Error: Unknown mesh type: "+geometryTemplate.name+"!!")
    return(objects)

def bf42_importGeometry(geometryTemplate, base_path, level, bf42_data, sceneScale = 1):
    if geometryTemplate.type in ["standardmesh", "animatedmesh", "treemesh"]:
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