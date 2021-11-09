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

def bf42_getCollectionByName(name,parentCollection = None, onlyCheckIfExists = False):
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
    if collection == None and not onlyCheckIfExists:
        collection = bpy.data.collections.new(name)
        parentCollection.children.link(collection)
    return(collection)

def bf42_getTexturePathByName(RelativeTexturePath):
    # texturepath info: "texture/buildings/house1" => TextureBaseDir = "texture", TextureName = "house1", RelativeTexturePath_sub = "buildings/house1"
    # if baseDir is in "texture" and alternativePaths
        # first check if name (not path) is in an alternativePath(from first to last mentioned)
        # if baseDir == "texture"
            # then check if filePath is in texture.rfa
        # for alt path (from first to last mentioned)
            # if baseDir == alternativePaths.name
                # then check if filePath is in alternativePaths["xxx"]
    # check in game-base dir
    
    RelativeTexturePath = RelativeTexturePath.strip("/")
    TextureBaseDir = RelativeTexturePath.split("/")[0]
    TextureName = RelativeTexturePath.split("/").pop()
    RelativeTexturePath_sub = RelativeTexturePath.split("/",1).pop()
    
    BF1942Settings = bpy.context.scene.BF1942Settings
    base_path = bpy.path.abspath(BF1942Settings.ImportConDir) # absolute paths: bf1942/levels/GC_Mos_Eisley/textures/tat_wood_1 (in rs)
    TextureDirList = loads(BF1942Settings.TextureDirList)
    alternativePaths = [(os.path.join(base_path, dir), dir.rstrip('/').split("/").pop()) for dir in TextureDirList] if TextureDirList != None else [] # textureManager.alternativePath bf1942/Levels/Liberation_of_Caen/Texture
    texturePath = os.path.join(base_path,"texture")
    
    alternativePathNames = [altPathName for (altPath, altPathName) in alternativePaths]
    
    for ext in ['.dds','.tga']:
        # this overwrite should actially only occur when the texture exists in the 'correct' location. But for performance I do it this way
        for (altPath, altPathName) in alternativePaths:
            texture_path = os.path.join(altPath,TextureName+ext)
            if os.path.isfile(texture_path):
                return(texture_path)
        if TextureBaseDir in ["texture"]+alternativePathNames:
            if TextureBaseDir == "texture":
                texture_path = os.path.join(texturePath,RelativeTexturePath_sub+ext)
                if os.path.isfile(texture_path):
                    return(texture_path)
            for (altPath, altPathName) in alternativePaths:
                if altPathName == TextureBaseDir:
                    texture_path = os.path.join(altPath,RelativeTexturePath_sub+ext)
                    if os.path.isfile(texture_path):
                        return(texture_path)
        else:
            texture_path = os.path.join(base_path,RelativeTexturePath+ext)
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
        directory = os.path.join(base_path,folderName)
        mesh_path = os.path.join(directory,geometryTemplate.file.strip("/")+ext)
        if os.path.isfile(mesh_path):
            rel_path = os.path.splitext(os.path.relpath(mesh_path,directory).replace("\\","/"))[0]
            return((mesh_path,rel_path))
        if level != "":
            directory = os.path.join(base_path,"Bf1942\\Levels\\"+level+"\\"+folderName)
            mesh_path = os.path.join(directory,geometryTemplate.file.strip("/")+ext)
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


#StandardMesh:
def bf42_getMeshesCollection():
    return(bf42_getCollectionByName('StandardMesh'))
    
def bf42_createMesh(vertices, faces, fileName, suffix, edges=[]):
    meshPath = fileName.split("/")
    fileName = meshPath.pop()
    meshCollection = bf42_getMeshesCollection()
    for dir in meshPath:
        meshCollection = bf42_getCollectionByName(dir,meshCollection)
    meshCollection = bf42_getCollectionByName(fileName,meshCollection)
    object = bf42_createUnlinkedObject(vertices, faces, fileName+suffix, edges)
    meshCollection.objects.link(object)
    return(object)


#TreeMesh:
def bf42_getTreeMeshesCollection():
    return(bf42_getCollectionByName('TreeMesh'))

def bf42_createTreeMesh(vertices, faces, fileName, suffix, edges=[]):
    meshPath = fileName.split("/")
    fileName = meshPath.pop()
    treeCollection = bf42_getTreeMeshesCollection()
    for dir in meshPath:
        treeCollection = bf42_getCollectionByName(dir,treeCollection)
    treeCollection = bf42_getCollectionByName(fileName,treeCollection)
    object = bf42_createUnlinkedObject(vertices, faces, fileName+suffix, edges)
    treeCollection.objects.link(object)
    return(object)

#AreaObject:
def bf42_getAreaObjectsCollection():
    return(bf42_getCollectionByName('Area Objects'))

def bf42_createAreaObject(vertices, edges, meshName="no name"):
    collection = bf42_getAreaObjectsCollection()
    object = bf42_createUnlinkedObject(vertices,[], meshName, edges)
    collection.objects.link(object)
    return(object)


#StaticObject:
def bf42_getStaticObjectsCollection():
    return(bf42_getCollectionByName('Static Objects'))

def bf42_addStaticObject(object):
    bf42_getStaticObjectsCollection().objects.link(object)


#MultieMeshObject:
def bf42_getMultiMeshObjectsCollection():
    return(bf42_getCollectionByName('Multi Mesh Objects'))

def bf42_addMultiMeshObject(collection, object, location = [0,0,0], rotation = [0,0,0]):
    new_object = object.copy()
    collection.objects.link(new_object)
    new_object.location = location
    new_object.rotation_euler = (-rotation[1]*pi/180, -rotation[2]*pi/180, -rotation[0]*pi/180)
    new_object.rotation_mode = "YXZ"
    return(collection)

