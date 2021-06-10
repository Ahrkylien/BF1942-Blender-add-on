import bpy
import os


def removesuffix(string, suffix):
    if suffix and string.endswith(suffix):
        return string[:-len(suffix)]
    else:
        return string[:]
        
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




def bf42_getCollection():
    try:
        bf42_collection = bpy.data.collections['bf42_environment']
    except:
        bf42_collection = bpy.data.collections.new('bf42_environment')
        bpy.context.scene.collection.children.link(bf42_collection)
    return(bf42_collection)

def bf42_getStaticObjectsCollection():
    bf42_collection = bf42_getCollection()
    try:
        bf42_static_collection = bpy.data.collections['bf42_static_objects']
    except:
        bf42_static_collection = bpy.data.collections.new('bf42_static_objects')
        bf42_collection.children.link(bf42_static_collection)
    return(bf42_static_collection)

def bf42_getObjectsCollection():
    bf42_collection = bf42_getCollection()
    try:
        bf42_object_collection = bpy.data.collections['bf42_objects']
    except:
        bf42_object_collection = bpy.data.collections.new('bf42_objects')
        bf42_collection.children.link(bf42_object_collection)
    return(bf42_object_collection)

def bf42_createObject(vertices,faces, name="no name", edges=[]):
    terrain_mesh = bpy.data.meshes.new(name)
    terrain_mesh.from_pydata(vertices, edges, faces)
    terrain_mesh.update()
    terrain_object = bpy.data.objects.new(name,terrain_mesh)
    bf42_addObject(terrain_object)
    return(terrain_object)

def bf42_addObject(object):
    bf42_object_collection = bf42_getObjectsCollection()
    bf42_object_collection.objects.link(object)

def bf42_addSpecialObject(object):
    bf42_collection = bf42_getCollection()
    bf42_collection.objects.link(object)

def bf42_addStaticObject(object):
    bf42_static_collection = bf42_getStaticObjectsCollection()
    bf42_static_collection.objects.link(object)

def bf42_duplicateSpecialObject(object,newName='tmp'):
    newObject = object.copy()
    newObject.data = object.data.copy()
    newObject.animation_data_clear()
    newObject.name=newName
    bf42_addSpecialObject(newObject)
    return(newObject)

def bf42_applyTransformObject(object):
    object.data.transform(object.matrix_world)
    object.matrix_world = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))

def bf42_triangulateObject(object):
    modifier = object.modifiers.new("tmp", "TRIANGULATE")
    old_active = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = object
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="tmp")
    bpy.context.view_layer.objects.active = old_active