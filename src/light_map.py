import bpy

from .misc import *


def light_map_export(objects_src, directory, sceneScale, option = "All - Diffuse", size = 128):
    bpy.context.scene.render.engine = 'CYCLES'

    #duplicate objects for bake and hide the oridginal ones:
    objects=[]
    objectsHiddenFromRender=[]
    for object_src in objects_src:
        if len(object_src.material_slots.values()) > 0:
            if object_src.material_slots[0].material != None:
                if "lightMap" in object_src.data.uv_layers:
                    image = bpy.data.images.new("lightmap_export_tmp", width = size, height = size, alpha=False)
                    objects.append((bf42_duplicateSpecialObject(object_src), image, object_src.name))
                    #Hide src object from bake render:
                    if object_src.hide_render == False:
                        objectsHiddenFromRender.append(object_src)
                        object_src.hide_render = True
    
    if len(objects) > 0:
        # make materials unique and add images:
        materials = []
        for (object, image, name) in objects:
            object.hide_render = False
            # activate lighmap uv
            object.data.uv_layers['lightMap'].active = True 
            # create matterial
            for matSlot in object.material_slots:
                material = matSlot.material.copy()
                matSlot.material = material
                material.use_nodes = True;
                node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
                node.image = image
                node.select = True
                material.node_tree.nodes.active = node
                materials.append(material)
        
        #bake objects:
        objects_selected = bpy.context.selected_objects.copy()
        object_active = bpy.context.view_layer.objects.active
        bpy.ops.object.select_all(action='DESELECT')
        for (object, image, name) in objects:
            object.select_set(True)
            bpy.context.view_layer.objects.active = object
        
        if option == "All":
            bpy.context.scene.render.bake.use_pass_indirect = True
            bpy.context.scene.render.bake.use_pass_direct = True
            bpy.context.scene.render.bake.use_pass_diffuse = True
            bpy.ops.object.bake(type='COMBINED')
        elif option == "All - Diffuse":
            bpy.context.scene.render.bake.use_pass_indirect = True
            bpy.context.scene.render.bake.use_pass_direct = True
            bpy.context.scene.render.bake.use_pass_diffuse = False
            bpy.ops.object.bake(type='COMBINED')
        elif option == "Environment":
            bpy.ops.object.bake(type='ENVIRONMENT')
        elif option == "Diffuse":
            bpy.context.scene.render.bake.use_pass_indirect = False
            bpy.context.scene.render.bake.use_pass_direct = False
            bpy.ops.object.bake(type='DIFFUSE')
        elif option == "Custom":
            bpy.ops.object.bake(type=bpy.context.scene.cycles.bake_type)

        bpy.ops.object.select_all(action='DESELECT')
        for object in objects_selected:
            object.select_set(True)
        bpy.context.view_layer.objects.active = object_active
        
        #save image externaly, and delete internal image and tmp object
        for (object, image, name) in objects:
            objectName = removesuffix(revomeBlenderSuffix(name),"_LOD1")
            pos = bf42_getPosition(object, sceneScale)
            filePath = directory+"\\"+objectName+"_"+pos.str_floor()+".tga"
            image.filepath_raw = filePath
            image.file_format = 'TARGA_RAW' #TARGA is compressed, but the image loads wrong into the game (flipped vertically)
            image.save()
            bpy.data.images.remove(image)
            bpy.data.objects.remove(object)
        
        #remove tmp materials:
        for material in materials:
            bpy.data.materials.remove(material)
        
        #un-Hide src object from bake render:
        for object in objectsHiddenFromRender:
            object_src.hide_render = False