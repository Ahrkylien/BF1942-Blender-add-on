# BF1942-Blender-add-on
A Battlefield 1942 import/export add-on for Blender.\
The add-on is still in a very early stage.
## Features:
- Heightmap (.raw) import/export
- StandardMesh (.sm & .rs) import/export
- TreeMesh (.tm) import/export
- Level Editing
	- Auto read (extracted) game files
	- Import static objects
	- Place new static objects
	- Export static objects
	- Export light maps
## Usage:
- download the add-on zip: https://github.com/Ahrkylien/BF1942-Blender-add-on/archive/refs/heads/main.zip
- open Blender
- in Blender go to: Edit -> Preferences -> Add-ons -> Install....
- select the zip you just downloaded
- now the Add-on is added. You only need to enable it by clicking the checkbox
- in Object-Mode on the right panel (press 'n') you will find the BF1942 menu
- for further usage read: https://github.com/Ahrkylien/BF1942-Blender-add-on/wiki/Usage
## ToDo:
- all imports:
	check if collection (where the new object is placed) is visable
	fix "not responding" for long imports. maybe:
	```
	bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
	```
- Heightmap import/export:
	- add support for materialSize and worldSize
- .sm import:
	- add Limited Disolve option
	- Tris to Quads option (Compare UVs)
	- let LODs share the same Material, option
	- correct vertex normals (COL)
	- correct face normals (LOD)
	- research matterial settings inside .sm (LOD), this really needs to be done to fix some weird alpha blending
	- add posibility too share Materials (with same properties) between different Objects
- .sm export:
	- LOD generation
	- create dummy Visible mesh if none supplied
	- separate Face by Angle
		``
		The LOD mesh separates faces whose face-to-face angle is greater than the smoothing angle.
		By separating it, the boundary between faces will appear angular in the game.
		``
	- Shadow LOD seperate faces (check if its needed, Dice Shadow meshes have this)
-	.tm import:
	- add Limited Disolve option
	- Tris to Quads option (Compare UVs)
	- let LODs share the same Material, option
-	.tm export:
	- order branches per angle on distance
	- the normal of the sprites doesnt matter but the export flips something randomly. This causes the Import of the flipped export the flip the normals (in bf42 the normals are not fliped).
	When exporting these imported fliped normals they dont show up in bf42 (the sprites)..
- Level Editing:
	- use texture directories
	- add heightmap import/export
	- add minimap render
	- add geometry.scale to object import/export
	- add geometry.color to object import/export ?for treeMeshes?
	- add filters for dropdown-list when adding new static objects
	- add more settings to lightmap export
	- Far LOD lightmap export
	```
	bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y
	camera = bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 1000*0.01), rotation=(0, 0, 0))
	bpy.context.object.data.type = 'ORTHO'
	bpy.context.object.data.ortho_scale = 2048*0.01
	bpy.context.object.data.shift_x = 0.5
	bpy.context.object.data.shift_y = 0.5
	bpy.context.object.data.clip_end = 1000
	```
- Area object import/export
- fill in: https://github.com/Ahrkylien/BF1942-Blender-add-on/wiki
  and add it to bl_info = {}
	- MaterialID list
