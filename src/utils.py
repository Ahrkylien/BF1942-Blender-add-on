import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, PointerProperty, StringProperty, FloatVectorProperty, EnumProperty
from bpy.types import Operator, Panel, PropertyGroup, AddonPreferences
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d, region_2d_to_location_3d
import os
from math import pi

from .heightmap import bf42_heightmap
from .standard_mesh import bf42_import_sm, bf42_export_sm
from .tree_mesh import bf42_import_tm, bf42_export_tm
from .bf42_script import *
from .light_map import light_map_export
from .place_object import bf42_placeObject
from .import_geometry import bf42_importGeometry
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
                        heightmap.addImportMapPath(os.path.join(ExportHeightmapFile,"Heightmap.raw"))
                        heightmap.generateMesh()
                else:
                    BF1942Settings.HeightmapObject = None
        return {'FINISHED'}
class BF1942_ExportSM(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.exportsm"
    bl_label = "Export BF1942 Standard Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings

        # not used:
        # ExportSMAutoGenLODs
        # ExportSMNumberOfLODs
        
        dir = bpy.path.abspath(BF1942Settings.ExportSMDir)
        name = BF1942Settings.ExportSMName
        BoundingBox_object = None
        if BF1942Settings.ExportSMUseCustomBoundingBox:
            BoundingBox_object = BF1942Settings.ExportSMCustomBoundingBox
        materialID = None
        if BF1942Settings.ExportSMForceMaterialID:
            materialID = BF1942Settings.ExportSMMaterialID
        COL_objects = []
        if BF1942Settings.ExportSMCOL1 != None:
            COL_objects.append(BF1942Settings.ExportSMCOL1)
            if BF1942Settings.ExportSMCOL2 != None:
                COL_objects.append(BF1942Settings.ExportSMCOL2)
        LOD_objects = []
        if BF1942Settings.ExportSMLOD1 != None:
            LOD_objects.append(BF1942Settings.ExportSMLOD1)
            if BF1942Settings.ExportSMLOD2 != None:
                LOD_objects.append(BF1942Settings.ExportSMLOD2)
                if BF1942Settings.ExportSMLOD3 != None:
                    LOD_objects.append(BF1942Settings.ExportSMLOD3)
                    if BF1942Settings.ExportSMLOD4 != None:
                        LOD_objects.append(BF1942Settings.ExportSMLOD4)
                        if BF1942Settings.ExportSMLOD5 != None:
                            LOD_objects.append(BF1942Settings.ExportSMLOD5)
                            if BF1942Settings.ExportSMLOD6 != None:
                                LOD_objects.append(BF1942Settings.ExportSMLOD6)
        SHADOW_objects = [] if BF1942Settings.ExportSMShadowLOD == None else [BF1942Settings.ExportSMShadowLOD]
        applyTrans = BF1942Settings.ExportSMApplyTransformation
        generateUV = BF1942Settings.ExportSMAutoGenUV
        sceneScale = BF1942Settings.sceneScale
        bf42_export_sm(dir, name, BoundingBox_object, COL_objects, LOD_objects, SHADOW_objects, materialID, applyTrans, generateUV, sceneScale)
        return {'FINISHED'}
class BF1942_ImportSM(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importsm"
    bl_label = "Import BF1942 Standard Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        path = bpy.path.abspath(BF1942Settings.ImportSMFile)
        add_BoundingBox = BF1942Settings.BoundingBox
        add_Collision = BF1942Settings.Collision
        add_Visible = BF1942Settings.Visible
        add_only_main_LOD = BF1942Settings.OnlyMainLOD
        add_Shadow = BF1942Settings.Shadow
        merge_shared_verticies = BF1942Settings.Merge_shared_verticies
        sceneScale = BF1942Settings.sceneScale
        bf42_import_sm(path, add_BoundingBox, add_Collision, add_Visible, add_only_main_LOD, add_Shadow, merge_shared_verticies,sceneScale)
        return {'FINISHED'}
class BF1942_ImportSM_Batch(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importsm_batch"
    bl_label = "Import BF1942 Standard Mesh Batch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        dir = bpy.path.abspath(BF1942Settings.ImportSMDir)
        add_BoundingBox = BF1942Settings.BoundingBox
        add_Collision = BF1942Settings.Collision
        add_Visible = BF1942Settings.Visible
        add_only_main_LOD = BF1942Settings.OnlyMainLOD
        add_Shadow = BF1942Settings.Shadow
        merge_shared_verticies = BF1942Settings.Merge_shared_verticies
        sceneScale = BF1942Settings.sceneScale
        for (dirPath, dirNames, fileNames) in os.walk(dir):
            for fileName in fileNames:
                basename = bpy.path.basename(fileName).rsplit('.',1)
                if len(basename) > 1:
                    if basename[1] == 'sm':
                        path = os.path.join(dirPath, fileName)
                        bf42_import_sm(path, add_BoundingBox, add_Collision, add_Visible, add_only_main_LOD, add_Shadow, merge_shared_verticies,sceneScale)
        return {'FINISHED'}
class BF1942_ImportTM(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importtm"
    bl_label = "Import BF1942 Tree Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        path =  bpy.path.abspath(BF1942Settings.ImportTMFile)
        add_BoundingBox = BF1942Settings.BoundingBoxesTM
        add_Collision = BF1942Settings.CollisionTM
        add_Visible = BF1942Settings.VisibleTM
        merge_shared_verticies = BF1942Settings.Merge_shared_verticiesTM
        sceneScale = BF1942Settings.sceneScale
        bf42_import_tm(path, add_BoundingBox, add_BoundingBox, add_Collision, add_Visible, merge_shared_verticies,sceneScale)
        return {'FINISHED'}
class BF1942_ImportTM_Batch(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importtm_batch"
    bl_label = "Import BF1942 Tree Mesh Batch"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        dir =  bpy.path.abspath(BF1942Settings.ImportTMDir)
        add_BoundingBox = BF1942Settings.BoundingBoxesTM
        add_Collision = BF1942Settings.CollisionTM
        add_Visible = BF1942Settings.VisibleTM
        merge_shared_verticies = BF1942Settings.Merge_shared_verticiesTM
        sceneScale = BF1942Settings.sceneScale
        pathList = []
        for (dirPath, dirNames, fileNames) in os.walk(dir):
            for fileName in fileNames:
                basename = bpy.path.basename(fileName).rsplit('.',1)
                if len(basename) > 1:
                    if basename[1] == 'tm':
                        pathList.append(os.path.join(dirPath, fileName))
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(pathList))
        for i, path in enumerate(pathList):
            bf42_import_tm(path, add_BoundingBox, add_BoundingBox, add_Collision, add_Visible, merge_shared_verticies,sceneScale)
            wm.progress_update(i)
        wm.progress_end()
        return {'FINISHED'}
class BF1942_ExportTM(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.exporttm"
    bl_label = "Export BF1942 Tree Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings

        dir = bpy.path.abspath(BF1942Settings.ExportTMDir)
        name = BF1942Settings.ExportTMName
        materialID = None
        if BF1942Settings.ExportTMForceMaterialID:
            materialID = BF1942Settings.ExportTMMaterialID
        AngleCount = BF1942Settings.ExportTMAngleCount
        COL_object = BF1942Settings.ExportTMCOL
        Branch_object = BF1942Settings.ExportTMBranch
        Trunk_object = BF1942Settings.ExportTMTrunk
        Sprite_object = BF1942Settings.ExportTMSprite
        applyTrans = BF1942Settings.ExportTMApplyTransformation
        sceneScale = BF1942Settings.sceneScale
        bf42_export_tm(dir, name, COL_object, Branch_object, Trunk_object, Sprite_object, materialID, AngleCount, applyTrans, sceneScale)
        return {'FINISHED'}
#### Level Editing: ####
def LevelListCallback(self, context):
    return [(item, item,"") for i, item in enumerate(loads(bpy.context.scene.BF1942Settings.LevelList))]
class BF1942_SelectLevel(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.selectlevel"
    bl_label = "Select Level"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "LevelListLocal"
    
    LevelListLocal: EnumProperty(
        items=LevelListCallback
    )

    def execute(self, context):
        bpy.context.scene.BF1942Settings.SelectedLevel = self.LevelListLocal
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
class BF1942_ReadConFiles(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.readconfiles"
    bl_label = "Read BF1942 Con files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        
        path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        
        data = bf42_readAllConFiles(path,level)
        BF1942Settings.AllBF42Data = data.dumps()
        
        #fill ObjectTemplateList:
        ObjectTemplateList = []
        for objectTemplate in data.objectTemplates:
            meshList = bf42_listAllGeometries(objectTemplate)
            ObjectTemplateList.append((objectTemplate.name,objectTemplate.type,len(meshList[0])))
        BF1942Settings.ObjectTemplateList = dumps(ObjectTemplateList)
        
        #fill TextureDirList:
        TextureDirList = []
        for TextureDir in data.textureManager_alternativePaths:
            TextureDirList.append(TextureDir)
        BF1942Settings.TextureDirList = dumps(TextureDirList)
        return {'FINISHED'}
class BF1942_ImportHeightMapLevel(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importheightmaplevel"
    bl_label = "Import BF1942 Heightmap for Level"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        data = BF42_data().loads(BF1942Settings.AllBF42Data)
        
        materialSize = 256
        worldSize = 1024
        yScale = BF1942Settings.yScale
        waterLevel = BF1942Settings.waterLevel
        
        for object in data.objects:
            if bf42_is_linked(object.template):
                if bf42_is_linked(object.template.geometry):
                    geometryTemplate = object.template.geometry
                    if geometryTemplate.type == "patchterrain":
                        materialSize = geometryTemplate.materialSize
                        worldSize = geometryTemplate.worldSize
                        yScale = geometryTemplate.yScale
                        waterLevel = geometryTemplate.waterLevel
                        break
        
        path = os.path.join(base_path,"Bf1942\\Levels\\"+level+"\\Heightmap.raw")
        if os.path.exists(path):
            xzScale = worldSize/materialSize/4
            heightmap = bf42_heightmap(yScale/xzScale, BF1942Settings.sceneScale*xzScale) # ugly trick to add resolution (xzScale) to sceneScale and yScale..
            heightmap.addImportMapPath(path)
            if heightmap.fileERROR:
                print(heightmap.fileERRORMessage)
            else:
                heightmap.generateMesh()
                heightmap.generateWaterMesh(waterLevel)
        return {'FINISHED'}
class BF1942_ImportLevelMeshes(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importlevelmeshes"
    bl_label = "Import Mehes for Level"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        data = BF42_data().loads(BF1942Settings.AllBF42Data)
        level = BF1942Settings.SelectedLevel
        preLoadAllMeshes = BF1942Settings.PreLoadAllMeshes
        sceneScale = BF1942Settings.sceneScale
        
        geometryTemplates = set()
        if not preLoadAllMeshes:
            objectTemplates = set()
            for object in data.objects:
                if bf42_is_linked(object.template):
                    objectTemplates.add(object.template)
            for objectTemplate in objectTemplates:
                if bf42_is_linked(objectTemplate.geometry):
                    geometryTemplates.add(objectTemplate.geometry)
        else:
            geometryTemplates = data.geometryTemplates
        
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(geometryTemplates))
        for i, geometryTemplate in enumerate(geometryTemplates):
            bf42_importGeometry(geometryTemplate, base_path, level, data, sceneScale)
            wm.progress_update(i)
        wm.progress_end()
        return {'FINISHED'}
class BF1942_ImportStaticObjects(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.importstaticobjects"
    bl_label = "Import BF1942 StaticObject.con"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        
        sceneScale = BF1942Settings.sceneScale
        loadFarLOD = False
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        data = BF42_data().loads(BF1942Settings.AllBF42Data)
        
        wm = bpy.context.window_manager
        wm.progress_begin(0, len(data.staticObjects))
        for i, object in enumerate(data.staticObjects):
            bf42_placeObject(object.template, sceneScale, base_path, level, data, object.absolutePosition, object.rotation, loadFarLOD)
            wm.progress_update(i)
        wm.progress_end()
        bf42_hide_bf42_multi_mesh_objects()
        return {'FINISHED'}
def ObjectTemplateListCallback(self, context):
    return [(item[0], item[0],"") for i, item in enumerate(loads(bpy.context.scene.BF1942Settings.ObjectTemplateList))]
class BF1942_AddStaticObject(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.addstaticobject"
    bl_label = "Add Static Object"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "ObjectTemplateListLocal"
    
    ObjectTemplateListLocal: EnumProperty(
        items=ObjectTemplateListCallback
    )

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        data = BF42_data().loads(BF1942Settings.AllBF42Data)
        sceneScale = BF1942Settings.sceneScale
        ObjectTemplate = data.getObjectTemplate(self.ObjectTemplateListLocal)
        print("step 1")
        if ObjectTemplate != None:
            object = bf42_placeObject(ObjectTemplate, sceneScale, base_path, level, data)
            if object != None:
                bpy.ops.object.select_all(action='DESELECT')
                object.select_set(True)
                BF1942Settings.SelectedObject = object
                print("step 2")
                # bpy.ops.bf1942.addstaticobject_modal_timer_operator()
                print("step 3")
        # return {'RUNNING_MODAL'}
        return(bpy.ops.bf1942.addstaticobject_modal_timer_operator())

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}
class BF1942_AddStaticObjectModalTimerOperator(bpy.types.Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.addstaticobject_modal_timer_operator"
    bl_label = "Add Object on Click"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None

    def modal(self, context, event):
        BF1942Settings = bpy.context.scene.BF1942Settings
        sceneScale = BF1942Settings.sceneScale
        print("step 4")
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE' and event.value == 'RELEASE':
            print("step 5")
            if context.area.type == 'VIEW_3D':
                print("step 6")
                r3d = context.space_data.region_3d
                x, y = event.mouse_region_x, event.mouse_region_y
                origin = region_2d_to_origin_3d(context.region, r3d, (x, y))
                direction = region_2d_to_vector_3d(context.region, r3d, (x, y))
                distance = 40*sceneScale
                loc = [origin[i]+direction[i]*distance for i in range(3)]
                mainCollection = bf42_getCollection()
                terrain_object = bf42_get_object(mainCollection,"terrain")
                if terrain_object != None:
                    scale = terrain_object.scale
                    result, location, normal, index = terrain_object.ray_cast([origin[i]/scale[i] for i in range(3)],direction)
                    if result:
                        loc = [location[i]*scale[i] for i in range(3)]
                loc = [max(loc[i],0) for i in range(3)]
                SelectedObject = bpy.context.scene.BF1942Settings.SelectedObject
                if SelectedObject != None:
                    SelectedObject.location=loc
                else:
                    return {'CANCELLED'}
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if context.area.type == 'VIEW_3D':
                self.cancel(context)
                return {'CANCELLED'}
        if event.type == 'TIMER':
            pass
        return {'PASS_THROUGH'}

    def execute(self, context):
        print("step x")
        if context.area.type != 'VIEW_3D':
            print("Must use in a 3d region")
            return {'CANCELLED'}
        wm = context.window_manager
        print("step xx")
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        print("step xxx")
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
class BF1942_ExportStaticObjects(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.exportstaticobjects"
    bl_label = "Export BF1942 StaticObject.con"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        sceneScale = BF1942Settings.sceneScale
        data = BF42_data().loads(BF1942Settings.AllBF42Data)
        
        if BF1942Settings.ExportConStaticFileBool:
            path = bpy.path.abspath(BF1942Settings.ExportConStaticFile)
        else:
            if level != "":
                path = os.path.join(base_path,"Bf1942\\Levels\\"+level+"\\StaticObjects.con")
            else:
                print("Error: No Level and no export file selected. Please select one")
                return {'CANCELLED'}
        objects = []
        
        StaticObject_collection = bf42_getStaticObjectsCollection()
        # static_object = zip(StaticObject_collection.children, StaticObject_collection.objects)
        for static_object in StaticObject_collection.objects:
            newObject = BF42_Object(removesuffix(revomeBlenderSuffix(static_object.name),"_LOD1"))
            newObject.absolutePosition = bf42_getPosition(static_object, sceneScale)
            newObject.rotation = bf42_getRotation(static_object)
            objects.append(newObject)
        bf42_writeStaticCon(path, objects, data)
        return {'FINISHED'}
class BF1942_ExportLightMaps(Operator):
    """An Operator for the BF1942 addon"""
    bl_idname = "bf1942.exportlightmaps"
    bl_label = "Export BF1942 LightMaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BF1942Settings = bpy.context.scene.BF1942Settings
        base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
        level = BF1942Settings.SelectedLevel
        sceneScale = BF1942Settings.sceneScale
        
        if BF1942Settings.ExportLightMapDirBool:
            path = bpy.path.abspath(BF1942Settings.LightMapDir)
        else:
            if level != "":
                path = os.path.join(base_path,"Bf1942\\Levels\\"+level+"\\ObjectLightmaps")
                if not os.path.exists(path):
                    os.makedirs(path)
            else:
                print("Error: No Level and no export file selected. Please select one")
                return {'CANCELLED'}
        
        StaticObject_objects = bf42_getStaticObjectsCollection().objects
        # StaticObject_objects = zip(StaticObject_collection.children, StaticObject_collection.objects)
        #duplicate all objects and their children:
        objects = []
        for object in StaticObject_objects:
            if object.instance_type == 'COLLECTION':
                if object.instance_collection != None:
                    for child in object.instance_collection.objects:
                        objects.append(bf42_duplicateSpecialObject(child))
                        objects[-1].location =  bf42_getPosition(child).rotate(bf42_getRotation(object)).add(bf42_getPosition(object)).toBlend()
                        bf42_applyRotation(objects[-1], bf42_getRotation(object).add(bf42_getRotation(child)))
            else:
                objects.append(bf42_duplicateSpecialObject(object))
        bf42_toggle_hide_static_objects(True)
        light_map_export(StaticObject_objects, path, sceneScale)
        bf42_toggle_hide_static_objects(False)
        for object in objects:
            bpy.data.objects.remove(object)
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
        col.prop(settings, 'TextureDirectory', text='Texture Folder')

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
        col.prop(settings, 'ImportHeightmapFile', text='File')
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
        col.prop(settings, 'ExportHeightmapFile', text='Folder')
        col.prop(settings, 'HeightmapObject', text='Terrain')
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
        col.prop(settings, 'BoundingBox', text='Bounding Box')
        col.prop(settings, 'Collision')
        col.prop(settings, 'Visible')
        col.prop(settings, 'OnlyMainLOD', text='Only Main LOD')
        col.prop(settings, 'Shadow')
        col.prop(settings, 'Merge_shared_verticies', text='Merge shared vertices')
        col.prop(settings, 'ImportSMFile', text='File')
        # row = layout.row(align=True)
        col.operator("bf1942.importsm", text="Import")
        col.prop(settings, 'ImportSMDir', text='Folder')
        col.operator("bf1942.importsm_batch", text="Import Batch")

class BF1942_PT_ExportSM(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Export Mesh"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        BF1942Settings = bpy.context.scene.BF1942Settings
        layout = self.layout
        
        col = layout.column(align=True)
        col.prop(settings, 'ExportSMDir', text='folder')
        col.prop(settings, 'ExportSMName', text='name')
        col.prop(settings, 'ExportSMUseCustomBoundingBox', text='use custom BoundingBox')
        if BF1942Settings.ExportSMUseCustomBoundingBox:
            col.prop(settings, 'ExportSMCustomBoundingBox', text='BoundingBox')
        col.prop(settings, 'ExportSMForceMaterialID', text='overide material ID')
        if BF1942Settings.ExportSMForceMaterialID:
            col.prop(settings, 'ExportSMMaterialID', text='MaterialID')
        col.prop(settings, 'ExportSMCOL1', text='COL1')
        if BF1942Settings.ExportSMCOL1 != None: #how does 3dsmax handle this?
            col.prop(settings, 'ExportSMCOL2', text='COL2')
        col.prop(settings, 'ExportSMAutoGenUV', text='Save lightMap UV')
        # col.prop(settings, 'ExportSMAutoGenLODs', text='auto genrate LODs 2,3,4,5,6')
        # col.prop(settings, 'ExportSMNumberOfLODs', text='min # of LODs')
        col.prop(settings, 'ExportSMLOD1', text='LOD1')
        LOD_count = 0
        if BF1942Settings.ExportSMLOD1 != None:
            LOD_count = 1
            col.prop(settings, 'ExportSMLOD2', text='LOD2')
            if BF1942Settings.ExportSMLOD2 != None:
                LOD_count = 2
                col.prop(settings, 'ExportSMLOD3', text='LOD3')
                if BF1942Settings.ExportSMLOD3 != None:
                    LOD_count = 3
                    col.prop(settings, 'ExportSMLOD4', text='LOD4')
                    if BF1942Settings.ExportSMLOD4 != None:
                        LOD_count = 4
                        col.prop(settings, 'ExportSMLOD5', text='LOD5')
                        if BF1942Settings.ExportSMLOD5 != None:
                            LOD_count = 5
                            col.prop(settings, 'ExportSMLOD6', text='LOD6')
                            if BF1942Settings.ExportSMLOD6 != None:
                                LOD_count = 6
        if BF1942Settings.ExportSMAutoGenLODs and BF1942Settings.ExportSMLOD1 != None:
            for i in range(BF1942Settings.ExportSMNumberOfLODs-LOD_count):
                col.label(text="LOD"+str(i+LOD_count+1)+": will be generated")
        col.prop(settings, 'ExportSMShadowLOD', text='ShadowLOD')
        col.prop(settings, 'ExportSMApplyTransformation', text='apply object transformation/scale')
        col.operator("bf1942.exportsm", text="Export")

class BF1942_PT_ImportTM(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Import Tree Mesh"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        layout = self.layout
        
        
        col = layout.column(align=True)
        col.prop(settings, 'BoundingBoxesTM', text='Bounding Boxes')
        col.prop(settings, 'CollisionTM', text='Collision')
        col.prop(settings, 'VisibleTM', text='Visible')
        col.prop(settings, 'Merge_shared_verticiesTM', text='Merge shared vertices')
        col.prop(settings, 'ImportTMFile', text='File')
        # row = layout.row(align=True)
        col.operator("bf1942.importtm", text="Import")
        col.prop(settings, 'ImportTMDir', text='Folder')
        col.operator("bf1942.importtm_batch", text="Import Batch")

class BF1942_PT_ExportTM(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Export Tree Mesh"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        BF1942Settings = bpy.context.scene.BF1942Settings
        layout = self.layout
        
        col = layout.column(align=True)
        col.prop(settings, 'ExportTMDir', text='folder')
        col.prop(settings, 'ExportTMName', text='name')
        col.prop(settings, 'ExportTMForceMaterialID', text='overide material ID')
        if BF1942Settings.ExportTMForceMaterialID:
            col.prop(settings, 'ExportTMMaterialID', text='MaterialID')
        col.prop(settings, 'ExportTMAngleCount', text='Angle count')
        col.prop(settings, 'ExportTMCOL', text='COL')
        col.prop(settings, 'ExportTMTrunk', text='Trunk')
        col.prop(settings, 'ExportTMBranch', text='Branch')
        col.prop(settings, 'ExportTMSprite', text='Sprite')
        col.prop(settings, 'ExportTMApplyTransformation', text='apply object transformation/scale')
        col.operator("bf1942.exporttm", text="Export")

class BF1942_PT_ImportCon(Panel):
    bl_space_type = "VIEW_3D"
    bl_context = "objectmode"
    bl_region_type = "UI"
    bl_label = "Level/Map Editing"
    bl_category = "BF1942"

    def draw(self, context):
        scn = context.scene
        settings = scn.BF1942Settings
        BF1942Settings = bpy.context.scene.BF1942Settings
        layout = self.layout
        
        col = layout.column(align=True)
        col.prop(settings, 'ImportConDir', text="Base Folder")
        if BF1942Settings.SelectedLevel != "":
            col.operator("bf1942.selectlevel", text="Selected Level: "+BF1942Settings.SelectedLevel)
        else:
            col.operator("bf1942.selectlevel", text="Select Level (can be empty)")
        col.operator("bf1942.readconfiles", text="Load Files")
        if BF1942Settings.AllBF42Data != "80034e2e":
            col.operator("bf1942.importheightmaplevel", text="Import Heightmap")
            # col.prop(settings, 'PreLoadAllMeshes', text='PreLoad ALL Meshes')
            # col.operator("bf1942.importlevelmeshes", text="Import (Tree)Meshes")
            col.operator("bf1942.importstaticobjects", text="Import Static Objects")
            
            col.operator("bf1942.addstaticobject", text="Add new static object")
            
            box = col.box()
            box.prop(settings, 'ExportConStaticFileBool', text='use custom export File')
            if BF1942Settings.ExportConStaticFileBool:
                box.prop(settings, 'ExportConStaticFile', text='StaticObjects Export File')
            box.operator("bf1942.exportstaticobjects", text="Export static objects")
            
            box = col.box()
            box.prop(settings, 'ExportLightMapDirBool', text='use custom export Folder')
            if BF1942Settings.ExportLightMapDirBool:
                box.prop(settings, 'LightMapDir', text='LightMap Export Folder')
            box.operator("bf1942.exportlightmaps", text="Export LightMaps")

class BF1942_PT_material(Panel):
    bl_idname = "MATERIAL_PT_BF1942"
    bl_label = "BF1942"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return(False)
        elif context.object.active_material is None:
            return(False)
        else:
            return(True)

    # def draw_header(self, context):
        # layout = self.layout
        # obj = context.object
        # layout.prop(obj, "select", text="") #rna_uiItemR: property not found: Object.select

    def draw(self, context):
        layout = self.layout

        ob = context.object
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        COL_box = layout.box()
        COL_box.label(text="For COL Meshes:", icon="OBJECT_DATA")
        COL_box.prop(ob.active_material.BF1942_sm_Properties, "MaterialID")
        
        
        
        LOD_box = layout.box()
        col  = LOD_box.column(align=True)
        col.label(text="For LOD Meshes:", icon="MATERIAL_DATA")
        col.prop(ob.active_material.BF1942_sm_Properties, "texture")
        
        col.prop(ob.active_material.BF1942_sm_Properties, "lighting")
        dif_box = LOD_box.box()
        dif_box.prop(ob.active_material.BF1942_sm_Properties, "materialDiffuse")
        
        col = LOD_box.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "lightingSpecular")
        spec_box = LOD_box.box()
        spec_box.prop(ob.active_material.BF1942_sm_Properties, "materialSpecularPower")
        spec_box.prop(ob.active_material.BF1942_sm_Properties, "materialSpecular")
        
        col = LOD_box.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "twosided")
        col.prop(ob.active_material.BF1942_sm_Properties, "envmap")
        
        col.prop(ob.active_material.BF1942_sm_Properties, "transparent")
        trans_box = LOD_box.box()
        trans_box.prop(ob.active_material.BF1942_sm_Properties, "depthWrite")
        blend_row = trans_box.column_flow(columns=2,align=True)
        blend_row.use_property_split = True
        blend_row.prop(ob.active_material.BF1942_sm_Properties, "blendSrc")
        blend_row.prop(ob.active_material.BF1942_sm_Properties, "blendDest")
        
        col = LOD_box.column(align=True)
        col.prop(ob.active_material.BF1942_sm_Properties, "textureFade")
        col.prop(ob.active_material.BF1942_sm_Properties, "alphaTestRef")











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
        default=False
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
        default = 12.5,
        min = 0
    )
    #for collision mesh:
    MaterialID : IntProperty(
        name="MaterialID",
        default = 45,
        min = 0
    )



def bf42_loadLevelList(self,context):
    BF1942Settings = bpy.context.scene.BF1942Settings
    base_path = bpy.path.abspath(BF1942Settings.ImportConDir)
    LevelList = []
    levelsDir = os.path.join(base_path,"bf1942/levels")
    if os.path.isdir(levelsDir):
        for dir_name in os.listdir(levelsDir):
            if os.path.isdir(os.path.join(levelsDir,dir_name)):
                LevelList.append(dir_name)
    BF1942Settings.LevelList = dumps(LevelList)
    
class BF1942Settings(PropertyGroup):

    ################# world settings ###################
    
    sceneScale : FloatProperty(
        name = "Scene Scale",
        description = "The scale factor of the Blender scene",
        default = 0.1,
        min = 0
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
    
    ################# heightmap settings ###################

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
    
    ################# .sm Import settings ###################
    
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

    Shadow : BoolProperty(
        name = "Shadow",
        description = "Shadow",
        default = False
        )

    Merge_shared_verticies : BoolProperty(
        name = "Merge_shared_verticies",
        description = "Merge shared verticies",
        default = True
        )
    
    ################# .sm Export settings ###################
    
    ExportSMDir : StringProperty(name = "ExportSMDir", description = "ExportSMDir", default = "", subtype="DIR_PATH")
    
    ExportSMName : StringProperty(name = "ExportSMName", description = "ExportSMName", default = "")

    ExportSMUseCustomBoundingBox : BoolProperty(name = "ExportSMUseCustomBoundingBox", description = "ExportSMUseCustomBoundingBox", default = False)
    
    ExportSMCustomBoundingBox : PointerProperty(type=bpy.types.Object)

    ExportSMForceMaterialID : BoolProperty(name = "ExportSMForceMaterialID", description = "ExportSMForceMaterialID", default = False)
    
    ExportSMMaterialID : IntProperty(name="ExportSMMaterialID", default = 45, min = 0)
    
    ExportSMCOL1 : PointerProperty(type=bpy.types.Object)
    
    ExportSMCOL2 : PointerProperty(type=bpy.types.Object)
    
    ExportSMLOD1 : PointerProperty(type=bpy.types.Object)

    ExportSMAutoGenUV : BoolProperty(name = "ExportSMAutoGenUV", description = "auto genrate lightMapUV when not existing", default = True)

    ExportSMAutoGenLODs : BoolProperty(name = "ExportSMAutoGenLODs", description = "ExportSMAutoGenLODs", default = False)

    ExportSMNumberOfLODs : IntProperty(name = "ExportSMNumberOfLODs", description = "ExportSMNumberOfLODs", default = 6, min = 0, max = 6)
    
    ExportSMLOD2 : PointerProperty(type=bpy.types.Object)
    
    ExportSMLOD3 : PointerProperty(type=bpy.types.Object)
    
    ExportSMLOD4 : PointerProperty(type=bpy.types.Object)
    
    ExportSMLOD5 : PointerProperty(type=bpy.types.Object)
    
    ExportSMLOD6 : PointerProperty(type=bpy.types.Object)
    
    ExportSMShadowLOD : PointerProperty(type=bpy.types.Object)

    ExportSMApplyTransformation : BoolProperty(name = "ExportSMApplyTransformation", description = "ExportSMApplyTransformation", default = True)

    ################# .tm Import settings ###################
    
    ImportTMFile : StringProperty(
        name = "ImportTMFile",
        description = "ImportTMFile",
        default = "",
        subtype="FILE_PATH"
        )
        
    ImportTMDir : StringProperty(
        name = "ImportTMDir",
        description = "ImportTMDir",
        default = "",
        subtype="DIR_PATH"
        )

    BoundingBoxesTM : BoolProperty(
        name = "BoundingBoxesTM",
        description = "BoundingBoxesTM",
        default = False
        )

    CollisionTM : BoolProperty(
        name = "CollisionTM",
        description = "CollisionTM",
        default = False
        )

    VisibleTM : BoolProperty(
        name = "VisibleTM",
        description = "VisibleTM",
        default = True
        )

    Merge_shared_verticiesTM : BoolProperty(
        name = "Merge_shared_verticiesTM",
        description = "Merge shared verticies",
        default = True
        )
    
    ################# .tm Export settings ###################
    
    ExportTMDir : StringProperty(name = "ExportTMDir", description = "ExportTMDir", default = "", subtype="DIR_PATH")
    
    ExportTMName : StringProperty(name = "ExportTMName", description = "ExportTMName", default = "")

    ExportTMForceMaterialID : BoolProperty(name = "ExportTMForceMaterialID", description = "ExportTMForceMaterialID", default = False)
    
    ExportTMMaterialID : IntProperty(name="ExportTMMaterialID", default = 45, min = 0)
    
    ExportTMAngleCount : IntProperty(name="ExportTMAngleCount", default = 8, min = 1)
    
    ExportTMCOL : PointerProperty(type=bpy.types.Object)
    
    ExportTMTrunk : PointerProperty(type=bpy.types.Object)
    
    ExportTMBranch : PointerProperty(type=bpy.types.Object)
    
    ExportTMSprite : PointerProperty(type=bpy.types.Object)

    ExportTMApplyTransformation : BoolProperty(name = "ExportTMApplyTransformation", description = "ExportTMApplyTransformation", default = True)
    
    ################# Script/Level import settings ###################
    
    ImportConDir : StringProperty(name = "ImportConDir", description = "Base directory for extracted bf1942", default = "", subtype="DIR_PATH", update=bf42_loadLevelList)
    
    # staticObjects export settings:
    ExportConStaticFileBool : BoolProperty(name = "ExportConStaticFileBool", description = "ExportConStaticFileBool", default = False)
    ExportConStaticFile : StringProperty(name = "ExportConStaticFile", description = "Custom file for export of static objects", default = "", subtype="FILE_PATH")
    
    # LightMaps export settings:
    LightMapDir : StringProperty(name = "LightMapDir", description = "LightMap Directory", default = "", subtype="DIR_PATH")
    ExportLightMapDirBool : BoolProperty(name = "ExportLightMapDirBool", description = "ExportConStaticFileBool", default = False)
    
    AllBF42Data : StringProperty(default = "80034e2e") #None, pickle and hex encoded
    LevelList : StringProperty(default = "80034e2e") #None, pickle and hex encoded
    TextureDirList : StringProperty(default = "80034e2e") #None, pickle and hex encoded
    SelectedLevel : StringProperty(default = "")
    PreLoadAllMeshes : BoolProperty(name = "PreLoadAllMeshes", description = "PreLoadAllMeshes", default = False)
    ObjectTemplateList : StringProperty(default = "80034e2e") #None, pickle and hex encoded
    SelectedObject : PointerProperty(type=bpy.types.Object)
    
    
    
    #################  ###################
    
    
    
    

    





class BF1942AddonPreferences(AddonPreferences):
    bl_idname = __package__.rsplit('.', 1)[0]

    # filepath: StringProperty(
        # name="Example File Path",
        # subtype='FILE_PATH',
    # )
    # number: IntProperty(
        # name="Example Number",
        # default=4,
    # )
    # boolean: BoolProperty(
        # name="Example Boolean",
        # default=False,
    # )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Here some settings wlll come (in the future)")
        # layout.prop(self, "filepath")
        # layout.prop(self, "number")
        # layout.prop(self, "boolean")