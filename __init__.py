# Addon Info
bl_info = {
    "name": "Battlefield 1942",
    "description": "This a start towards a complete Battlefield 1942 addon",
    "author": "Henk <Discord: Arkyliën#6833>",
    "version": (4, 0),
    "blender": (2,  81, 0),
    "location": "View 3D > Properties Panel",
    "support": "COMMUNITY",
    "wiki_url": "http://github.com/Ahrkylien/BF1942-Blender-add-on",
    "tracker_url": "https://github.com/Ahrkylien/BF1942-Blender-add-on/issues",
    "category": "Import-Export",
    }

import bpy
from .src.utils import *

classes = (
    BF1942Settings,
    BF1942_sm_Properties,
    BF1942_PT_worldSettings,
    
    BF1942_ImportHeightMap,
    BF1942_ExportHeightMap,
    BF1942_PT_ImportHeightmap,
    BF1942_PT_ExportHeightmap,
    
    BF1942_ImportSM,
    BF1942_ImportSM_Batch,
    BF1942_ExportSM,
    BF1942_PT_ImportSM,
    BF1942_PT_ExportSM,
    
    BF1942_ImportTM,
    BF1942_ImportTM_Batch,
    BF1942_ExportTM,
    BF1942_PT_ImportTM,
    BF1942_PT_ExportTM,
    
    BF1942_ReadConFiles,
    BF1942_SelectLevel,
    BF1942_ImportHeightMapLevel,
    BF1942_ImportLevelMeshes,
    BF1942_ImportStaticObjects,
    BF1942_AddStaticObject,
    BF1942_AddStaticObjectModalTimerOperator,
    BF1942_ExportStaticObjects,
    BF1942_ExportLightMaps,
    BF1942_PT_ImportCon,
    
    BF1942_TextureSubstract,
    BF1942_TextureDenoise,
    BF1942_TextureAverage,
    BF1942_TextureRAWToTGA,
    BF1942_PT_Convert,
    
    BF1942_PT_material,
    
    BF1942AddonPreferences,
    )

register, unregister = bpy.utils.register_classes_factory(classes)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.BF1942Settings = PointerProperty(type=BF1942Settings)
    bpy.types.Material.BF1942_sm_Properties = PointerProperty(type=BF1942_sm_Properties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.BF1942Settings
    del bpy.types.Material.BF1942_sm_Properties