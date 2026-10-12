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
## Skeleton, animation and skin (.ske, .baf, .skn)

Set **Scene Scale** (default 0.1) before importing or exporting. It applies to all three formats.

### Skeleton (.ske)
- **Import:** creates an armature named after the file. A `Bip01` root (player skeleton) is turned -90° about X so the character stands upright.
- **Export:** writes the armature's bones from their rest pose.
- **Bones** (import option):
  - **Extrapolate bones** (default): when a bone's axis nearly meets its child's axis, the tail moves onto that axis.
  - **Extrapolate and Connect bones**: as above, and a child whose head lies on its parent bone is connected to it.
  - **Pure**: bones use the exact axes from the file. No tail moves and no connections, so bones may not touch their children.

### Animation (.baf)
- **Import:** applies the animation to the **Armature** field, which the skeleton import fills in. Creates an action named after the file and makes it the armature's active action. Bones the armature doesn't have are skipped and listed in a warning. If needed, the scene's start frame is lowered to 0 and its end frame is raised to the last animation frame.
- **Existing animation:** nothing is overwritten. Importing again creates a new action. The previous action stays in the file but is no longer active. Without a **Fake User** (shield icon in the Action Editor) it is dropped on a later save. Turn on Fake User before importing to keep it.
- **Finding an action:** in the **Action Editor** (Dope Sheet mode), the action dropdown lists the actions in the file. The Outliner's **Blender File** view lists them too. With **Export all actions** on, the Animation export panel lists the actions that animate the armature.
- **Export:** select the **Armature**. With **Export all actions**, each action is written to its own file. Otherwise the action chosen in **Action** is written.

### Skin (.skn)
- **Import:** select the **Mesh** and the **Armature**. Import the matching .sm first, because vertices are matched by position. The mesh keeps its .sm geometry as the basis and is folded onto the rest pose in the shape key **BF1942 rest** (value 1.0).
- **Export:** select the **Armature** and the **Mesh**. Writes vertex positions and weights. Per-bone values come from the **BF1942 rest** shape key if present, otherwise from the basis.

### Limitations
- **.ske:** the Extrapolate options (used during import) change bone directions by up to about 0.1°. Use **Pure** for an exact round trip.
- **.skn:** for vertices weighted to more than one bone, the per-bone values are recalculated on export, so they can differ slightly from the source file. The rest pose is unchanged.
- **.baf:** bones missing from the armature are not exported.

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
