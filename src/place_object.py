import bpy

from .bf42_script import bf42_vec3, bf42_listAllGeometries
from .misc import *

def bf42_placeObject(objectTemplate, sceneScale = 1, position = None, rotation = None, loadFarLOD = False):
    if position == None:
        position = bf42_vec3([0,0,0])
    if rotation == None:
        rotation = bf42_vec3([0,0,0])
        
    mesh_collection = bf42_getMeshesCollection()
    treeMesh_collection = bf42_getTreeMeshesCollection()
    multiMeshObjectsCollection = bf42_getMultiMeshObjectsCollection()
    staticObjectsCollection = bf42_getStaticObjectsCollection()
        
    meshList = bf42_listAllGeometries(objectTemplate)
    if meshList != [[],[]]:
        if meshList[0] == []: #also check if mesh meshList[0][0] is at 0,0,0!!
            print("Warning: "+objectTemplate.name+" has no close-LOD Meshes in LodObject!!")
        meshes = meshList[0]
        if loadFarLOD and meshList[1] != []:
            meshes = meshList[1]
        
        blend_objects = []
        for mesh in meshes:
            meshFound = False
            if mesh[1] == "standardmesh":
                selected_mesh_collection = mesh_collection
            elif mesh[1] == "treemesh":
                selected_mesh_collection = treeMesh_collection
            else:
                print("Error: Unknown mesh type: "+mesh[1]+"!!")
            if mesh[1] in ["standardmesh", "treemesh"]:
                for blend_collection in selected_mesh_collection.children:
                    for blend_object in blend_collection.objects:
                        if removesuffix(revomeBlenderSuffix(blend_object.name),["_LOD1","_Branch","_Trunk","_Sprite","_Billboard"]).lower() == mesh[0]:
                            blend_objects.append((blend_object, mesh))
                            meshFound = True
                            if mesh[1] == "standardmesh":
                                break
                    if meshFound:
                        break
            if not meshFound:
                print("Error: "+mesh[1]+" '"+mesh[0]+"' is not loaded into Blender!!")
        
        if len(blend_objects) != 1:
            MultiMeshCollection = bf42_getMultiMeshObjectsCollection()
            meshCollection_exists = False
            for meshCollection in MultiMeshCollection.children:
                if revomeBlenderSuffix(meshCollection.name) == objectTemplate.name:
                    meshCollection_exists = True
                    break;
            meshCollection = bf42_getCollectionByName(objectTemplate.name,MultiMeshCollection)
            if not meshCollection_exists:
                for blend_object in blend_objects:
                    bf42_addMultiMeshObject(meshCollection, blend_object[0], blend_object[1][2].toBlend(sceneScale), blend_object[1][3].lst())
            instance_obj = bpy.data.objects.new(objectTemplate.name, None)
            instance_obj.instance_collection = meshCollection
            instance_obj.instance_type = 'COLLECTION'
            if len(blend_objects) != 0: #show placeholder?
                instance_obj.empty_display_size = 0
        else:
            instance_obj = blend_objects[0][0].copy()
    else:
        MultiMeshCollection = bf42_getMultiMeshObjectsCollection()
        meshCollection = bf42_getCollectionByName(objectTemplate.name,MultiMeshCollection)
        instance_obj = bpy.data.objects.new(objectTemplate.name, None)
        instance_obj.instance_collection = meshCollection
        instance_obj.instance_type = 'COLLECTION'
        print("Error: "+objectTemplate.name+" does not have any meshes!!")
    instance_obj.location = position.toBlend(sceneScale)
    bf42_applyRotation(instance_obj,rotation)
    instance_obj.name = objectTemplate.name
    instance_obj.empty_display_type = 'SINGLE_ARROW'
    staticObjectsCollection.objects.link(instance_obj)
    return(instance_obj)