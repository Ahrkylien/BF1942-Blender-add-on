import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, PointerProperty, StringProperty, FloatVectorProperty, EnumProperty
from bpy.types import Operator, Panel, PropertyGroup
import os
from math import pi

from .heightmap import bf42_heightmap
from .standard_mesh import bf42_import_sm
from .staticObjects import bf42_ParseCon
from .misc import *

#Operators
class BF1942_ImportHeightMap(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importheightmap"
    bl_label = "Import BF1942 Heightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        ImportHeightmapFile = bpy.path.abspath(BF1942Settings.ImportHeightmapFile)
        if os.path.exists(ImportHeightmapFile):
            heightmap = bf42_heightmap(BF1942Settings.yScale,BF1942Settings.sceneScale)
            heightmap.addImportMapPath(ImportHeightmapFile)
            if heightmap.fileERROR:
                print(heightmap.fileERRORMessage)
            else:
                heightmap.generateMesh()
                if BF1942Settings.addWorldSize:
                    BF1942Settings.WorldSize = heightmap.worldSize
                if BF1942Settings.addWater:
                    heightmap.generateWaterMesh(BF1942Settings.waterLevel)
            del heightmap
        return {'FINISHED'}
class BF1942_ExportHeightMap(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.exportheightmap"
    bl_label = "Export BF1942 Heightmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        ExportHeightmapFile = bpy.path.abspath(BF1942Settings.ExportHeightmapFile)
        if os.path.exists(os.path.dirname(ExportHeightmapFile)) and ExportHeightmapFile != "":
            selectedObject = BF1942Settings.HeightmapObject
            if selectedObject != None:
                selectedObject = bpy.data.objects.get(selectedObject.name)
                if selectedObject != None:
                    heightmap = bf42_heightmap(BF1942Settings.yScale,BF1942Settings.sceneScale)
                    heightmap.setWorldSize(BF1942Settings.WorldSize)
                    heightmap.addExportMapPath(ExportHeightmapFile)
                    heightmap.generateHeightmap(selectedObject)
                    if BF1942Settings.AddHeightmapAfterExport:
                        heightmap.addImportMapPath(ExportHeightmapFile)
                        heightmap.generateMesh()
                    del heightmap
                else:
                    BF1942Settings.HeightmapObject = None
        return {'FINISHED'}
class BF1942_ImportSM(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importsm"
    bl_label = "Import BF1942 Standard Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        path = BF1942Settings.ImportSMFile
        add_BoundingBox = BF1942Settings.BoundingBox
        add_Collision = BF1942Settings.Collision
        add_Visible = BF1942Settings.Visible
        add_only_main_LOD = BF1942Settings.OnlyMainLOD
        merge_shared_verticies = BF1942Settings.Merge_shared_verticies
        sceneScale = BF1942Settings.sceneScale
        bf42_import_sm(path, add_BoundingBox, add_Collision, add_Visible, add_only_main_LOD, merge_shared_verticies,sceneScale)
        return {'FINISHED'}
class BF1942_ImportSM_Batch(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importsm_batch"
    bl_label = "Import BF1942 Standard Mesh Batch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        dir = BF1942Settings.ImportSMDir
        add_BoundingBox = BF1942Settings.BoundingBox
        add_Collision = BF1942Settings.Collision
        add_Visible = BF1942Settings.Visible
        add_only_main_LOD = BF1942Settings.OnlyMainLOD
        merge_shared_verticies = BF1942Settings.Merge_shared_verticies
        sceneScale = BF1942Settings.sceneScale
        print("")
        for (dirPath, dirNames, fileNames) in os.walk(dir):
            for fileName in fileNames:
                basename = bpy.path.basename(fileName).rsplit('.',1)
                if len(basename) > 1:
                    if basename[1] == 'sm':
                        path = os.path.join(dirPath, fileName)
                        bf42_import_sm(path, add_BoundingBox, add_Collision, add_Visible, add_only_main_LOD, merge_shared_verticies,sceneScale)
        return {'FINISHED'}
class BF1942_ImportStaticObjects(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importstaticobjects"
    bl_label = "Import BF1942 StaticObject.con"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        
        path = BF1942Settings.ImportConFile
        sceneScale = BF1942Settings.sceneScale
        
        objects_not_found = []
        static_objects = bf42_ParseCon(path)
        object_collection = bf42_getObjectsCollection()
        for static_object in static_objects:
            for object in object_collection.objects:
                if removesuffix(object.name,"_LOD0").lower() == static_object.name.lower():
                    v=static_object.absolutePosition
                    r=static_object.rotation
                    new_object = object.copy()
                    new_object.location = (v.x*sceneScale, v.y*sceneScale, v.z*sceneScale)
                    new_object.rotation_euler = (-r.z*pi/180, -r.y*pi/180, -r.x*pi/180)
                    new_object.rotation_mode = "YXZ"
                    bf42_addStaticObject(new_object)
                    break
            if removesuffix(object.name,"_LOD0").lower() != static_object.name.lower():
                if not static_object.name.lower() in objects_not_found:
                    objects_not_found.append(static_object.name.lower())
        if objects_not_found != []:
            popupMessage("warnings",["Some Objects not found, check console message"])
            print("\n ####### These Static Objects don't exist in bf42_environment->bf42_objects:")
            for objects_name in objects_not_found:
                print(objects_name)
        return {'FINISHED'}








# Panels
class BF1942_PT_worldSettings(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "World Settings"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout

        col = layout.column(align=True)
#        col.prop(settings, 'coverage', slider=True)
        col.prop(settings, 'sceneScale')
        col.prop(settings, 'WorldSize')
        col.prop(settings, 'yScale')
        col.prop(settings, 'waterLevel')
        col.prop(settings, 'TextureDirectory')

#        layout.use_property_split = True
#        layout.use_property_decorate = False
#        flow = layout.grid_flow(row_major=True, columns=0, even_columns=False, even_rows=False, align=True)
#        col = flow.column()
#        col.prop(settings, 'vertices')

#        row = layout.row(align=True)
#        row.scale_y = 1.5
#        row.operator("bf1942.importheightmap", text="Add Snow", icon="FREEZE")

class BF1942_PT_ImportHeightmap(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Import Heightmap"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout
        
        
        col = layout.column(align=True)
        col.prop(settings, 'ImportHeightmapFile')
        col.prop(settings, 'addWater')
        col.prop(settings, 'addWorldSize')
        row = layout.row(align=True)
        row.operator("bf1942.importheightmap", text="Import")

class BF1942_PT_ExportHeightmap(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Export Heightmap"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout
        
        
        col = layout.column(align=True)
        col.prop(settings, 'ExportHeightmapFile')
        col.prop(settings, 'HeightmapObject')
        col.prop(settings, 'AddHeightmapAfterExport')
        row = layout.row(align=True)
        row.operator("bf1942.exportheightmap", text="Export")

class BF1942_PT_ImportSM(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Import Mesh"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout
        
        
        col = layout.column(align=True)
        col.prop(settings, 'BoundingBox')
        col.prop(settings, 'Collision')
        col.prop(settings, 'Visible')
        col.prop(settings, 'OnlyMainLOD')
        col.prop(settings, 'Merge_shared_verticies')
        col.prop(settings, 'ImportSMFile')
        # row = layout.row(align=True)
        col.operator("bf1942.importsm", text="Import")
        col.prop(settings, 'ImportSMDir')
        col.operator("bf1942.importsm_batch", text="Import Batch")

class BF1942_PT_ImportCon(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Import StaticObjects.con"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout
        
        col = layout.column(align=True)
        col.prop(settings, 'ImportConFile')
        col.operator("bf1942.importstaticobjects", text="Import")

class BF1942_PT_material(Panel):
    bl_idname = "MATERIAL_PT_BF1942"
    bl_label = "BF1942"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    # def draw_header(self, context):
        # layout = self.layout
        # obj = context.object
        # layout.prop(obj, "select", text="") #rna_uiItemR: property not found: Object.select

    def draw(self, context):
        layout = self.layout

        ob = context.object
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        col = layout.column(align=True)
        
        col.prop(ob.active_material.BF1942_sm_Properties, "texture")
        
        col.prop(ob.active_material.BF1942_sm_Properties, "lighting")
        dif_box = layout.box()
        dif_box.prop(ob.active_material.BF1942_sm_Properties, "materialDiffuse")
        
        col = layout.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "lightingSpecular")
        spec_box = layout.box()
        spec_box.prop(ob.active_material.BF1942_sm_Properties, "materialSpecularPower")
        spec_box.prop(ob.active_material.BF1942_sm_Properties, "materialSpecular")
        
        col = layout.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "twosided")
        col.prop(ob.active_material.BF1942_sm_Properties, "envmap")
        
        col.prop(ob.active_material.BF1942_sm_Properties, "transparent")
        trans_box = layout.box()
        trans_box.prop(ob.active_material.BF1942_sm_Properties, "depthWrite")
        blend_row = trans_box.column_flow(columns=2,align=True)
        blend_row.use_property_split = True
        blend_row.prop(ob.active_material.BF1942_sm_Properties, "blendSrc")
        blend_row.prop(ob.active_material.BF1942_sm_Properties, "blendDest")
        
        col = layout.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "textureFade")
        col.prop(ob.active_material.BF1942_sm_Properties, "alphaTestRef")
        col.label(text = "Generated texture path: ")
        col.prop(ob.active_material.BF1942_sm_Properties, "useCustomTexturePath")
        col.prop(ob.active_material.BF1942_sm_Properties, "customTexturePath")











# Properties
def bf42_rs_twosided(self,context):
    if hasattr(context, 'material'):
        context.material.use_backface_culling = not self.twosided
def bf42_rs_transparent(self,context):
    if hasattr(context, 'material'):
        if self.transparent:
            context.material.blend_method = 'BLEND'
        else:
            context.material.blend_method = 'OPAQUE'
def bf42_rs_textureFade(self,context):
    if hasattr(context, 'material'):
        if self.textureFade:
            context.material.blend_method = 'BLEND'
        else:
            context.material.blend_method = 'OPAQUE'

class BF1942_sm_Properties(PropertyGroup):
    # BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty, FloatVectorProperty
    # https://docs.blender.org/api/current/bpy.types.Property.html#bpy.types.Property.subtype
    # https://docs.blender.org/api/current/bpy.props.html
    
    blend_modes = [
        ("sourceAlphaSat", "sourceAlphaSat", ''),
        ("invDestAlpha", "invDestAlpha", ''),
        ("destAlpha", "destAlpha", ''),
        ("invDestColor", "invDestColor", ''),
        ("destColor", "destColor", ''),
        ("invSourceAlpha", "invSourceAlpha", ''),
        ("sourceAlpha", "sourceAlpha", ''),
        ("invSourceColor", "invSourceColor", ''),
        ("sourceColor", "sourceColor", ''),
        ("one", "one", ''),
        ("zero", "zero", '')
    ]
    
    texture : StringProperty(
        name="texture",
        default=""
    )
    transparent : BoolProperty(
        name="transparent",
        default=False,
        update=bf42_rs_transparent
    )
    lighting : BoolProperty(
        name="lighting",
        default=True
    )
    lightingSpecular : BoolProperty(
        name="lightingSpecular",
        default=True
    )
    twosided : BoolProperty(
        name="twosided",
        default=False,
        update=bf42_rs_twosided
    )
    envmap : BoolProperty(
        name="envmap",
        default=False
    )
    textureFade : BoolProperty(
        name="textureFade",
        default=False
    )
    depthWrite : BoolProperty(
        name="depthWrite",
        default=True
    )
    blendSrc : EnumProperty(
        items = blend_modes,
        name="blendSrc",
        description="blend modes",
        default="invSourceAlpha"
    )
    blendDest : EnumProperty(
        items = blend_modes,
        name="blendDest",
        description="blend modes",
        default="sourceAlpha"
    )
    alphaTestRef : FloatProperty(
        name="alphaTestRef",
        default = 0,
        min = 0,
        max = 1
    )
    materialDiffuse : FloatVectorProperty(
        name="materialDiffuse",
        default=(1, 1, 1), 
        min = 0,
        max = 1,
        subtype = "COLOR"
    )
    materialSpecular : FloatVectorProperty(
        name="materialSpecular",
        default=(1, 1, 1), 
        min = 0,
        max = 1,
        subtype = "COLOR"
    )
    materialSpecularPower : FloatProperty(
        name="materialSpecularPower",
        default = 1,
        min = 0
    )
    useCustomTexturePath : BoolProperty(
        name="useCustomTexturePath",
        default=False
    )
    customTexturePath : StringProperty(
        name="customTexturePath",
        default = "",
    )

class BF1942Settings(PropertyGroup):
    sceneScale : FloatProperty(
        name = "Scene Scale",
        description = "The scale factor of the Blender scene",
        default = 0.01,
        min = 0
        )
    ImportHeightmapFile : StringProperty(
        name = "ImportHeightmapFile",
        description = "ImportHeightmapFile",
        default = "",
        subtype="FILE_PATH"
        )
    ExportHeightmapFile : StringProperty(
        name = "ExportHeightmapFile",
        description = "ExportHeightmapFile",
        default = "",
        subtype="FILE_PATH"
        )
    
    WorldSize : IntProperty(
        name = "WorldSize",
        description = "WorldSize in Init/Terrain.con",
        default = 1024,
        min = 0
        )

    yScale : FloatProperty(
        name = "yScale",
        description = "yScale in Init/Terrain.con",
        default = 0.6,
        min = 0
        )

    waterLevel : FloatProperty(
        name = "waterLevel",
        description = "waterLevel in Init/Terrain.con",
        default = 0
        )
        
    TextureDirectory : StringProperty(
        name = "TextureDirectory",
        description = "TextureDirectory",
        default = "",
        subtype="DIR_PATH"
        )

    addWater : BoolProperty(
        name = "Add Water",
        description = "Add Water mesh",
        default = False
        )

    addWorldSize : BoolProperty(
        name = "Add WorldSize to World Settings",
        description = "Add WorldSize to World Settings",
        default = True
        )

    HeightmapObject : PointerProperty(
        type=bpy.types.Object
        )
    
    AddHeightmapAfterExport : BoolProperty(
        name = "Import heightmap after export",
        description = "Import heightmap after export",
        default = True
        )
        
    ImportSMFile : StringProperty(
        name = "ImportSMFile",
        description = "ImportSMFile",
        default = "",
        subtype="FILE_PATH"
        )
        
    ImportSMDir : StringProperty(
        name = "ImportSMDir",
        description = "ImportSMDir",
        default = "",
        subtype="DIR_PATH"
        )

    BoundingBox : BoolProperty(
        name = "BoundingBox",
        description = "BoundingBox",
        default = False
        )

    Collision : BoolProperty(
        name = "Collision",
        description = "Collision",
        default = False
        )

    Visible : BoolProperty(
        name = "Visible",
        description = "Visible",
        default = True
        )

    OnlyMainLOD : BoolProperty(
        name = "OnlyMainLOD",
        description = "OnlyMainLOD",
        default = True
        )

    Merge_shared_verticies : BoolProperty(
        name = "Merge_shared_verticies",
        description = "Merge shared verticies",
        default = True
        )

    ImportConFile : StringProperty(
        name = "ImportConFile",
        description = "Import StaticObjects.con",
        default = "",
        subtype="FILE_PATH"
        )