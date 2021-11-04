import bpy
import os
from math import pi
import pickle

from .bf42_script import bf42_vec3


#method to store objects as strings:
def dumps(objectToDump):
    return(pickle.dumps(objectToDump).hex())
def loads(stringToLoad):
    return(pickle.loads(bytes.fromhex(stringToLoad)))


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

def bf42_getTextureDirs():
    # ToDo: relative paths: ../../bf1942/levels/Floating_Archipelago/menu/serverInfo.dds
    BF1942Settings = bpy.context.scene.BF1942Settings
    base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
    TextureDirList = loads(BF1942Settings.TextureDirList)
    TextureDirList = [os.path.join(base_path, dir) for dir in TextureDirList] if TextureDirList != None else [] # textureManager.alternativePath bf1942/Levels/Liberation_of_Caen/Texture
    TextureDirList.append(os.path.join(base_path,"texture"))
    TextureDirList.append(base_path) # absolute paths: bf1942/levels/GC_Mos_Eisley/textures/tat_wood_1 (in rs)
    TextureDirList.insert(0,bpy.path.abspath(BF1942Settings.TextureDirectory))
    return(TextureDirList)

def bf42_getTexturePathByName(textureName):
    for dir in bf42_getTextureDirs():
        for ext in ['.dds','.tga']:
            texture_path = os.path.join(dir,textureName+ext)
            if os.path.isfile(texture_path):
                return(texture_path)
    return(None)

def bf42_getMeshPath(geometryTemplate):
    if geometryTemplate.type in ["standardmesh", "animatedmesh", "treemesh"]:
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        if geometryTemplate.type in ["standardmesh", "animatedmesh"]:
            folderName = "StandardMesh"
            ext = ".sm"
        elif geometryTemplate.type == "treemesh":
            folderName = "treeMesh"
            ext = ".tm"
        if level != "":
            directory = os.path.join(base_path,"Bf1942\\Levels\\"+level+"\\"+folderName)
            mesh_path = os.path.join(directory,geometryTemplate.file+ext)
            if os.path.isfile(mesh_path):
                rel_path = os.path.splitext(os.path.relpath(mesh_path,directory).replace("\\","/"))[0]
                return((mesh_path,rel_path))
        directory = os.path.join(base_path,folderName)
        mesh_path = os.path.join(directory,geometryTemplate.file+ext)
        if os.path.isfile(mesh_path):
            rel_path = os.path.splitext(os.path.relpath(mesh_path,directory).replace("\\","/"))[0]
            return((mesh_path,rel_path))
    return((None,None))
    
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

def bf42_duplicateSpecialObject(object, newName=None):
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
    
def bf42_createMesh(vertices, faces, fileName, meshName="no name", edges=[]): #change to bf42_createMesh
    meshesCollection = bf42_getMeshesCollection()
    meshCollection = bf42_getCollectionByName(fileName,meshesCollection)
    object = bf42_createUnlinkedObject(vertices,faces, meshName, edges)
    meshCollection.objects.link(object)
    return(object)


#TreeMesh:
def bf42_getTreeMeshesCollection():
    return(bf42_getCollectionByName('bf42_tree_meshes'))

def bf42_createTreeMesh(vertices, faces, fileName, meshName="no name", edges=[]):
    treesCollection = bf42_getTreeMeshesCollection()
    treeCollection = bf42_getCollectionByName(fileName,treesCollection)
    object = bf42_createUnlinkedObject(vertices, faces, meshName, edges)
    treeCollection.objects.link(object)
    return(object)

#AreaObject:
def bf42_getAreaObjectsCollection():
    return(bf42_getCollectionByName('bf42_area_objects'))

def bf42_createAreaObject(vertices, edges, meshName="no name"):
    collection = bf42_getAreaObjectsCollection()
    object = bf42_createUnlinkedObject(vertices,[], meshName, edges)
    collection.objects.link(object)
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

