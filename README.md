# BF1942-Blender-add-on
A Battlefield 1942 import/export add-on for Blender.\
The add-on is still in a very early stage.
## Features:
- Heightmap.raw import/export
- mesh (.sm and .rs) import/export
- staticObject.con import/export
## Usage:
- download the add-on zip: https://github.com/Ahrkylien/BF1942-Blender-add-on/archive/refs/heads/main.zip
- open Blender
- in Blender go to: Edit -> Preferences -> Add-ons -> Install....
- select the zip you just downloaded
- now the Add-on is added. You only need to enable it by clicking the checkbox
- in Object-Mode on the right pannel (press 'n') you will find the BF1942 menu
## ToDo:
- .sm import:
	- correct vertex normals (COL)
	- correct face normals (LOD)
	- research matterial settings inside .sm (LOD)
	- let LODs share the same Material
	- let materials share the same textures
- .sm export:
	- LOD generation
	- create dummy Visible mesh if none supplied
	- Separate Face by Angle
		``
		The LOD mesh separates faces whose face-to-face angle is greater than the smoothing angle.
		By separating it, the boundary between faces will appear angular in the game.
		``
	- Shadow LOD seperate faces (check if its needed, Dice Shadow meshes have this)
- staticObject.con import
	- support Template structure readout or .lst readout
	- support Collections (bundles)
- staticObject.con export
	- support Collections (bundles)
	- support linked translation (translation of parent object)
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
	- MaterialID list
