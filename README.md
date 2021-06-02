# BF1942-Blender-add-on
A Battlefield 1942 import/export add-on for Blender.\
The add-on is still in a very early stage.
## Features:
- Heightmap.raw import
- Heightmap.raw export
- .sm import
- staticObject.con import
## ToDo:
- add .sm export
```
  https://blenderartists.org/t/different-ways-to-create-mesh-objects/496955/12
```
- staticObject.con export
- add minimap render
```
    bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y
    camera = bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 1000*0.01), rotation=(0, 0, 0))
    bpy.context.object.data.type = 'ORTHO'
    bpy.context.object.data.ortho_scale = 2048*0.01
    bpy.context.object.data.shift_x = 0.5
    bpy.context.object.data.shift_y = 0.5
    bpy.context.object.data.clip_end = 1000
```
- fill in: https://github.com/Ahrkylien/BF1942-Blender-add-on/wiki
  and add it to bl_info = {}
