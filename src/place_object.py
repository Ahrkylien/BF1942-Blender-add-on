import bpy

from .bf42_script import bf42_vec3, bf42_listAllGeometries, bf42_listAllGeometries_new
from .area_object import bf42_importAreaObject
from .import_geometry import bf42_importGeometry
from .misc import *

def bf42_placeObject(objectTemplate, sceneScale, base_path, level, bf42_data, position = None, rotation = None, loadFarLOD = False):
    if position == None:
        position = bf42_vec3([0,0,0])
    if rotation == None:
        rotation = bf42_vec3([0,0,0])
        
    MultiMeshObjectsCollection = bf42_getMultiMeshObjectsCollection()
    staticObjectsCollection = bf42_getStaticObjectsCollection()
    
    meshList = bf42_listAllGeometries_new(objectTemplate)
    if meshList != [[],[]]:
        if meshList[0] == []: #also check if mesh meshList[0][0] is at 0,0,0!!
            print("Warning: "+objectTemplate.name+" has no close-LOD Meshes in LodObject!!")
        meshes = meshList[0]
        if loadFarLOD and meshList[1] != []:
            meshes = meshList[1]
            
        blend_objects = []
        for geometryTemplate, pos, rot in meshes:
            geometryTemplate_blend_objects = bf42_importGeometry(geometryTemplate, base_path, level, bf42_data, sceneScale)
            for blend_object in geometryTemplate_blend_objects:
                blend_objects.append((blend_object, pos, rot))
            if geometryTemplate_blend_objects == []:
                print("Error: "+geometryTemplate.type+" '"+geometryTemplate.name+"' can not be loaded into Blender!!")
        
        if len(blend_objects) != 1:
            meshCollection_exists = False
            for meshCollection in MultiMeshObjectsCollection.children:
                if revomeBlenderSuffix(meshCollection.name) == objectTemplate.name:
                    meshCollection_exists = True
                    break;
            meshCollection = bf42_getCollectionByName(objectTemplate.name,MultiMeshObjectsCollection)
            if not meshCollection_exists:
                for blend_object, pos, rot in blend_objects:
                    bf42_addMultiMeshObject(meshCollection, blend_object, pos.toBlend(sceneScale), rot.lst())
            instance_obj = bpy.data.objects.new(objectTemplate.name, None)
            instance_obj.instance_collection = meshCollection
            instance_obj.instance_type = 'COLLECTION'
            if len(blend_objects) != 0: #show placeholder?
                instance_obj.empty_display_size = 0
        else:
            instance_obj = blend_objects[0][0].copy()
    elif objectTemplate.type == "areaobject":
        areaObject = bf42_importAreaObject(objectTemplate, sceneScale)
        instance_obj = areaObject.copy()
    else:
        meshCollection = bf42_getCollectionByName(objectTemplate.name,MultiMeshObjectsCollection)
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