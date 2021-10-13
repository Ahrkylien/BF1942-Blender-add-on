import bpy
import os
from math import pi

from .bf42_script import bf42_vec3

popupMessages = []
def draw_popupMessage(self, context):
    for popupMessage in popupMessages:
        self.layout.label(text=popupMessage)
def popupMessage(titleText,popupMessages_loc):
    global popupMessages
    if not popupMessages_loc == []:
        popupMessages = popupMessages_loc
        bpy.context.window_manager.popup_menu(draw_popupMessage, title=titleText, icon='INFO')

def bf42_isFloat(val):
    try: 
        float(val)
        return True
    except ValueError:
        return False

def removesuffix(string, suffixes):
    if isinstance(suffixes, str):
        suffixes = [suffixes]
    for suffix in suffixes:
        if suffix and string.endswith(suffix):
            return string[:-len(suffix)]
    return string[:]
def revomeBlenderSuffix(name):
    nameL = name.rsplit('.', 1)
    if len(nameL) == 2:
        if nameL[1].isnumeric():
            name = nameL[0]
    return(name)

def bf42_get_object(collection, name):
    object = collection.objects.get(name)
    if object != None:
        return(object)
    for object in collection.objects:
        if revomeBlenderSuffix(object.name) == name:
            return(object)
    return(None)

def bf42_getCollectionByName(name,parentCollection = None):
    if parentCollection == None:
        if name == 'bf42_environment':
            parentCollection = bpy.context.scene.collection
        else:
            parentCollection = bf42_getCollectionByName('bf42_environment')
    collection = parentCollection.children.get(name)
    if collection == None:
        for collection_child in parentCollection.children:
            if revomeBlenderSuffix(collection_child.name) == name:
                collection = collection_child
                break
    if collection == None:
        collection = bpy.data.collections.new(name)
        parentCollection.children.link(collection)
    return(collection)

def bf42_getTexturePathByName(textureName):
    BF1942Settings = bpy.context.scene.BF1942Settings
    defaultTexPath = BF1942Settings.TextureDirectory
    FILE_PATH_dds=bpy.path.abspath(defaultTexPath+textureName+".dds")
    if os.path.isfile(FILE_PATH_dds):
        return(FILE_PATH_dds)
    FILE_PATH_tga=bpy.path.abspath(defaultTexPath+textureName+".tga")
    if os.path.isfile(FILE_PATH_tga):
        return(FILE_PATH_tga)
    return(False)
    
def bf42_getPosition(object, sceneScale = 1):
    p = object.location
    return(bf42_vec3((p.x/sceneScale,p.z/sceneScale,p.y/sceneScale)))

def bf42_getRotation(object):
    if 'Z' in object.rotation_mode:
        q = object.rotation_euler.to_quaternion()
    else:
        q = object.rotation_quaternion
    r = q.to_euler("YXZ")
    return(bf42_vec3((-r.z/pi*180,-r.x/pi*180,-r.y/pi*180)))

def bf42_applyRotation(object, bf42_rotation):
    r=bf42_rotation
    object.rotation_euler = (-r.y*pi/180, -r.z*pi/180, -r.x*pi/180)
    object.rotation_mode = "YXZ"

def bf42_applyTransformObject(object):
    object.data.transform(object.matrix_world)
    object.matrix_world = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))

def bf42_triangulateObject(object):
    modifier = object.modifiers.new("tmp", "TRIANGULATE")
    old_active = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = object
    if bpy.app.version >= (2, 91, 0):
        bpy.ops.object.modifier_apply(modifier="tmp")
    else:
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="tmp")
    bpy.context.view_layer.objects.active = old_active

def bf42_toggle_hide_layer_collection(name="", exclude=True):
    for layer_collection in bpy.context.view_layer.layer_collection.children:
        if layer_collection.name == "bf42_environment":
            for layer_collection in layer_collection.children:
                if layer_collection.name == name:
                    layer_collection.exclude = exclude
                    break
            break

def bf42_hide_bf42_multi_mesh_objects(exclude=True):
    bf42_toggle_hide_layer_collection("bf42_multi_mesh_objects", exclude)

def bf42_toggle_hide_static_objects(exclude=True):
    bf42_toggle_hide_layer_collection("bf42_static_objects", exclude)

def bf42_createUnlinkedObject(vertices,faces, name="no name", edges=[]):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()
    object = bpy.data.objects.new(name,mesh)
    return(object)


#Global:
def bf42_getCollection():
    return(bf42_getCollectionByName('bf42_environment'))

def bf42_addSpecialObject(object):
    bf42_getCollection().objects.link(object)

def bf42_duplicateSpecialObject(object,newName=None):
    newObject = object.copy()
    newObject.data = object.data.copy()
    newObject.animation_data_clear()
    if newName != None:
        newObject.name=newName
    bf42_addSpecialObject(newObject)
    return(newObject)


#Mesh:
def bf42_getMeshesCollection():
    return(bf42_getCollectionByName('bf42_meshes'))
    
def bf42_createMesh(vertices,faces, fileName, meshName="no name", edges=[]): #change to bf42_createMesh
    meshesCollection = bf42_getMeshesCollection()
    meshCollection = bf42_getCollectionByName(fileName,meshesCollection)
    object = bf42_createUnlinkedObject(vertices,faces, meshName, edges)
    meshCollection.objects.link(object)
    return(object)


#TreeMesh:
def bf42_getTreeMeshesCollection():
    return(bf42_getCollectionByName('bf42_tree_meshes'))

def bf42_createTreeMesh(vertices,faces, fileName, meshName="no name", edges=[]):
    treesCollection = bf42_getTreeMeshesCollection()
    treeCollection = bf42_getCollectionByName(fileName,treesCollection)
    object = bf42_createUnlinkedObject(vertices,faces, meshName, edges)
    treeCollection.objects.link(object)
    return(object)


#StaticObject:
def bf42_getStaticObjectsCollection():
    return(bf42_getCollectionByName('bf42_static_objects'))

def bf42_addStaticObject(object):
    bf42_getStaticObjectsCollection().objects.link(object)


#MultieMeshObject:
def bf42_getMultiMeshObjectsCollection():
    return(bf42_getCollectionByName('bf42_multi_mesh_objects'))

def bf42_addMultiMeshObject(collection, object, location = [0,0,0], rotation = [0,0,0]):
    new_object = object.copy()
    collection.objects.link(new_object)
    new_object.location = location
    new_object.rotation_euler = (-rotation[1]*pi/180, -rotation[2]*pi/180, -rotation[0]*pi/180)
    new_object.rotation_mode = "YXZ"
    return(collection)

