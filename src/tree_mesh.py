import os
import bpy
from math import sin, cos, pi

from .standard_mesh import *

class tm_Geometries:
    def __init__(self, vertexValues=None, vertexNormals=None, vertexDiffuse32=None, vertexTextureUV=None, spriteVertexOffsets=None):
        self.geometries = []
        self.numVertices = 0
        
        #SharedVertices:
        self.vertexValues = [] if vertexValues is None else vertexValues
        self.vertexNormals = [] if vertexNormals is None else vertexNormals
        self.vertexDiffuse32 = [] if vertexDiffuse32 is None else vertexDiffuse32
        self.vertexTextureUV = [] if vertexTextureUV is None else vertexTextureUV
        self.spriteVertexOffsets = [] if spriteVertexOffsets is None else spriteVertexOffsets
        
        self.numFaceValues = 0
    def read_1(self,f):
        for i in range(4):
            self.geometries.append(tm_Geometry().read_1(f))
            
            if i == 3 and self.geometries[-1].count != 0:
                print("Unexpected, there is a billboard mesh?")
        return(self)
    def read_2(self,f,angleCnt):
        self.numVertices = sm_i(f)
        for i in range(self.numVertices):
            realVert = sm_f(f,3)
            self.vertexValues.append((realVert[0],realVert[2],realVert[1]))
            Vnormal = sm_f(f,3)
            self.vertexNormals.append((Vnormal[0],Vnormal[2],Vnormal[1])) # 0 for sprites
            self.vertexDiffuse32.append(sm_i(f)) #0x80808080 for Trunk, 0 for sprite
            self.vertexTextureUV.append(sm_f(f,2))
            self.spriteVertexOffsets.append(sm_f(f,2)) #(0,0) for trunk and branch
            if not self.vertexDiffuse32[-1] in [0x80808080,0]:
                print("Unexpected, vertexDiffuse32 is: "+str(self.vertexDiffuse32[-1]))
        
        self.numFaceValues = sm_i(f)
        
        # dubug check:
        treeMesh_by_3dsmax = False
        meshes = []
        totalNumFaceValues = 0
        for i, geometry in enumerate(self.geometries):
            for mesh in geometry.meshes:
                meshes.append((i, mesh))
                totalNumFaceValues += mesh.numFaces*3*(8 if i in [0,2] else 1)
        if totalNumFaceValues != self.numFaceValues:
            print("Unexpected, numFaceValues is not '"+str(self.numFaceValues)+"'?: "+str(totalNumFaceValues))
        for i, (geomeType, mesh) in enumerate(meshes):
            try:
                next_indexStart = meshes[i+1][1].indexStart
            except:
                next_indexStart = self.numFaceValues
            numAngles = (next_indexStart-mesh.indexStart)/3/mesh.numFaces
            if geomeType in [0,2] and numAngles != angleCnt:
                print("Unexpected, angleCount for geomeType '"+str(geomeType)+"' is not '"+str(angleCnt)+"'?: "+str(numAngles))
                treeMesh_by_3dsmax = True
            if geomeType in [1] and numAngles != 1:
                print("Unexpected, angleCount for geomeType '"+str(geomeType)+"' is not '1'?: "+str(numAngles))
                if numAngles == 8:
                    treeMesh_by_3dsmax = True
        
        for i in range(4):
            for mesh in self.geometries[i].meshes:
                startOfSection = f.tell()
                mesh.read_2(f)
                # for Branches and Sprites there are angleCnt submeshes:
                if i in [0,2]: #maybe 3 also??
                    for j in range(angleCnt-1):
                        if treeMesh_by_3dsmax and i == 2: #treeMesh_by_3dsmax has a weird/unexpected EoF
                            f.seek(startOfSection)
                        mesh.read_2(f)
                # 3dsmax export has an error:
                if treeMesh_by_3dsmax:
                    if i in [1]:
                        for j in range(angleCnt-1):
                            mesh.read_2(f)

class tm_Geometry:
    def __init__(self):
        self.count = 0
        self.numFaceValues = 0
        self.meshes = []
    def read_1(self,f):
        self.count = sm_i(f)
        for i in range(self.count):
            self.meshes.append(tm_LOD_mesh().read_1(f))
        return(self)

class tm_LOD_mesh:
    def __init__(self, faces=None):
        self.indexStart = 0
        self.numFaces = 0
        self.textureNameLen = 0
        self.textureName = ""
        
        self.faceValues = []
        
        #not in sm (generated in read_2())
        self.faces = [] if faces is None else faces
    def read_1(self,f):
        self.indexStart = sm_i(f)
        self.numFaces = sm_i(f)
        self.textureNameLen = sm_i(f)
        self.textureName = sm_s(f, self.textureNameLen)
        return(self)
    def read_2(self,f):
        for i in range(self.numFaces):	
            faceValues = sm_i_short(f,3)
            self.faces.append((faceValues[0],faceValues[2],faceValues[1]))
        return(self)

#helper classes:
# sprites:
    # material:
        # texturename
        # sprites:
            # sprite:
                # centerCoordinate
                # vertexCoordinateOffsets
                # vertexNormals
                # vertexTextureUV
                # faces:
                    # face
class tm_sprites:
    def __init__(self):
        self.materialMeshes = []
    def loadObject(self,Sprite_object):
        vertices = []
        vertexNormals = []
        vertexTextureUV = []
        spriteVertexOffsets = []
        vertices_ref = []
        textureNames = []
        faces = []
        spriteBoundingBox = [0]*6
        if Sprite_object != None:
            object = bf42_duplicateSpecialObject(Sprite_object)
            bpy.ops.object.select_all(action='DESELECT')
            object.select_set(True)
            bpy.context.view_layer.objects.active = object
            bpy.ops.mesh.separate(type='MATERIAL')
            spriteMaterials = bpy.context.selected_objects.copy()
            for spriteMaterial in spriteMaterials:
                self.materialMeshes.append(tm_sprites_material_mesh().loadObject(spriteMaterial))
        return(self)
class tm_sprites_material_mesh:
    def __init__(self):
        self.texturename = ""
        self.sprites = []
    def loadObject(self,spriteMaterial):
        material = spriteMaterial.data.materials[0]
        self.texturename = "texture/"+material.BF1942_sm_Properties.texture
        bpy.ops.object.select_all(action='DESELECT')
        spriteMaterial.select_set(True)
        bpy.context.view_layer.objects.active = spriteMaterial
        bpy.ops.mesh.separate(type='LOOSE')
        spriteObjects = bpy.context.selected_objects.copy()
        materialFaces = []
        for spriteObject in spriteObjects:
            self.sprites.append(tm_sprite().loadObject(spriteObject))
        return(self)
    def getOrderByAngle(self,angle,angleCount):
        order = []
        angleRad = ((angle+0.5)/angleCount)*2*pi
        print("### angle")
        print(angleRad)
        for i, sprite in enumerate(self.sprites):
            centerCoordinate = sprite.centerCoordinate
            print("### centerCoordinate")
            print(centerCoordinate)
            depth_i = centerCoordinate[0]*sin(angleRad) + centerCoordinate[2]*cos(angleRad)
            print("### depth_i")
            print(depth_i)
            j = len(order)
            for k_j, k in enumerate(order):
                depth_j = self.sprites[k].centerCoordinate[0]*sin(angleRad) + self.sprites[k].centerCoordinate[2]*cos(angleRad)
                print("### depth_j")
                print(depth_j)
                if depth_j < depth_i:
                    j = k_j
                    break
            order.insert(j,i)
        print("### order")
        print(order)
        order.reverse()
        return(order)
class tm_sprite:
    def __init__(self):
        self.centerCoordinate = [0,0,0]
        self.vertexCoordinateOffsets = []
        self.vertexTextureUV = []
        self.faces = []
    def loadObject(self,spriteObject):
        mesh = spriteObject.data
        texutre_uv_layer = None
        for uv_layer in mesh.uv_layers:
            if texutre_uv_layer == None:
                texutre_uv_layer = uv_layer # use first uv_layer if no textureMap is existing
            if uv_layer.name == "textureMap":
                texutre_uv_layer = uv_layer
        vertices_ref = []
        vertexCoordinates = []
        for polygon in mesh.polygons:
            face = []
            for loop_index in polygon.loop_indices:
                vertex_index = mesh.loops[loop_index].vertex_index
                vertex = mesh.vertices[vertex_index]
                if texutre_uv_layer == None:
                    vertexTextureUVco = (0,0)
                else:
                    vertexTextureUVco = (texutre_uv_layer.data[loop_index].uv[0],1-texutre_uv_layer.data[loop_index].uv[1])
                ref = (vertex_index) # dont weld vertices for sprites
                try:
                    vertices_ref_index = vertices_ref.index(ref)
                except ValueError:
                    vertexCoordinates.append([vertex.co[0],vertex.co[2],vertex.co[1]])
                    self.vertexTextureUV.append(vertexTextureUVco)
                    vertices_ref.append(ref)
                    vertices_ref_index = len(vertices_ref)-1
                face.append(vertices_ref_index)
            self.faces.append((face[0],face[2],face[1]))
        bpy.data.objects.remove(spriteObject)
        # add offset:
        self.centerCoordinate = [float(sum(col))/len(col) for col in zip(*vertexCoordinates)]
        for vertexCoordinate in vertexCoordinates:
            self.vertexCoordinateOffsets.append([vertexCoordinate[0]-self.centerCoordinate[0],vertexCoordinate[1]-self.centerCoordinate[1]])
        return(self)


def bf42_import_tm(path, add_BoundingBox, add_BoundingBoxLeaves, add_Collision, add_Visible, merge_shared_verticies, sceneScale, name = None):
    path = bpy.path.abspath(path)
    try:
        f = open(path, 'rb')
    except IOError:
        print("File not accessible")
    else:
        print("################### IMPORT ####################")
        bpy.ops.object.select_all(action='DESELECT')
        if name == None:
            filePath = os.path.splitext(bpy.path.basename(path))[0]
        else:
            filePath = name
        fileName = filePath.split("/").pop()
        
        f.seek(0,2)
        fileSize = f.tell()
        f.seek(0)
        header = sm_i(f) #3 in export
        if header == 3:
            unknown1 = sm_i(f) #0 in export
            if unknown1 != 0:
                print("Unexpected, unknown1 is not 0?: "+str(unknown1))
            angleCnt = sm_i(f) #number of billboard angles, 8 in export
            if angleCnt != 8:
                print("Unexpected, angleCnt is not 8?: "+str(angleCnt))
            bboxMesh = sm_f(f,6)
            if add_BoundingBox:
                BB = bboxMesh
                vertices = [(BB[0],BB[2],BB[1]),(BB[0],BB[5],BB[1]),(BB[3],BB[5],BB[1]),(BB[3],BB[2],BB[1]),
                            (BB[0],BB[2],BB[4]),(BB[0],BB[5],BB[4]),(BB[3],BB[5],BB[4]),(BB[3],BB[2],BB[4])]
                edges = [(0,1),(1,2),(2,3),(3,0),
                        (4,5),(5,6),(6,7),(7,4),
                        (0,4),(1,5),(2,6),(3,7),]
                BoundingBox_object = bf42_createTreeMesh(vertices,[], filePath, '_BoundingBox',edges = edges)
                BoundingBox_object.scale = (sceneScale,sceneScale,sceneScale)
            bboxSpriteLeaves = sm_f(f,6)
            if add_BoundingBoxLeaves:
                BB = bboxSpriteLeaves
                vertices = [(BB[0],BB[2],BB[1]),(BB[0],BB[5],BB[1]),(BB[3],BB[5],BB[1]),(BB[3],BB[2],BB[1]),
                            (BB[0],BB[2],BB[4]),(BB[0],BB[5],BB[4]),(BB[3],BB[5],BB[4]),(BB[3],BB[2],BB[4])]
                edges = [(0,1),(1,2),(2,3),(3,0),
                        (4,5),(5,6),(6,7),(7,4),
                        (0,4),(1,5),(2,6),(3,7),]
                BoundingBox_object = bf42_createTreeMesh(vertices,[], filePath, '_BoundingBoxSpriteLeaves',edges = edges)
                BoundingBox_object.scale = (sceneScale,sceneScale,sceneScale)
            
            #Header data of Visible geometry types
            #0 = Branch -> each mesh has angleCnt submeshes
            #1 = Trunk
            #2 = Sprite -> each mesh has angleCnt submeshes -> per sprite 4 vertices at same pos with 2 faces per angle (faces dont move vertices between angles)
            #3 = Billboard
            geometries = tm_Geometries().read_1(f)

            #Collision Mesh data, same as .sm only no sizeOfSection in front of it
            collisionMesh = sm_COL_mesh().read(f)
            if add_Collision and collisionMesh.exists:
                vertices = []
                faces = []
                for vertex in collisionMesh.vertices:
                    vertices.append((vertex.vertex[0],vertex.vertex[2],vertex.vertex[1]))
                for face in collisionMesh.faces:
                    faces.append(face.vertices)
                object = bf42_createTreeMesh(vertices,faces, filePath, '_COL')
                object.scale = (sceneScale,sceneScale,sceneScale)
                mesh = object.data
                materialIDs = []
                for i, polygon in enumerate(mesh.polygons):
                    materialID = collisionMesh.faces[i].materialID
                    if not materialID in materialIDs:
                        materialIDs.append(materialID)
                    materialIndex = materialIDs.index(materialID)
                    polygon.material_index = materialIndex

            #LOD, almost the same as .sm LOD.read_2
            #All vertex_data of all meshes: (4 parts, n meshes, angleCnt submeshes, n faces)
            geometries.read_2(f,angleCnt)
            
            
            branches = geometries.geometries[0]
            for j, mesh in enumerate(branches.meshes):
                lenFaceSection = int(len(mesh.faces)/angleCnt)
                # for k in range(angleCnt):
                for k in range(1):
                    faceSection = mesh.faces[k*lenFaceSection:(k+1)*lenFaceSection]
                    object = bf42_createTreeMesh(geometries.vertexValues,faceSection, filePath, '_Branch_'+str(j+1))
                    object.scale = (sceneScale,sceneScale,sceneScale)
                    rs_matterial = bf42_material("")
                    texture_split = mesh.textureName.split('/',1)
                    if len(texture_split) == 2:
                        rs_matterial.texture = texture_split[1]
                    rs_matterial.textureFullPath = mesh.textureName
                    rs_matterial.twosided = True
                    rs_matterial.transparent = True
                    mat = bf42_add_sm_Material(object.data, rs_matterial, fileName+'_Branch_'+str(j+1))
                    texutre_uv_layer = object.data.uv_layers.new(name='textureMap')
                    for loop in object.data.loops:
                        texutre_uv_layer.data[loop.index].uv = (geometries.vertexTextureUV[loop.vertex_index][0],-geometries.vertexTextureUV[loop.vertex_index][1])
                    object.select_set(True)
                    bpy.context.view_layer.objects.active = object
            if len(branches.meshes) > 0:
                bpy.ops.object.join()
                object.name = fileName+'_Branch'
                object.data.name = fileName+'_Branch'
                bpy.ops.object.editmode_toggle()
                if merge_shared_verticies:
                    bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                bpy.ops.mesh.delete_loose()
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
            
            trunks = geometries.geometries[1]
            for j, mesh in enumerate(trunks.meshes):
                object = bf42_createTreeMesh(geometries.vertexValues,mesh.faces, filePath, '_Trunk_'+str(j+1))
                object.scale = (sceneScale,sceneScale,sceneScale)
                rs_matterial = bf42_material("")
                texture_split = mesh.textureName.split('/',1)
                if len(texture_split) == 2:
                    rs_matterial.texture = texture_split[1]
                rs_matterial.textureFullPath = mesh.textureName
                rs_matterial.twosided = True
                rs_matterial.transparent = True
                mat = bf42_add_sm_Material(object.data, rs_matterial, fileName+'_Trunk_'+str(j+1))
                texutre_uv_layer = object.data.uv_layers.new(name='textureMap')
                for loop in object.data.loops:
                    texutre_uv_layer.data[loop.index].uv = (geometries.vertexTextureUV[loop.vertex_index][0],-geometries.vertexTextureUV[loop.vertex_index][1])
                object.select_set(True)
                bpy.context.view_layer.objects.active = object
            if len(trunks.meshes) > 0:
                bpy.ops.object.join()
                object.name = fileName+'_Trunk'
                object.data.name = fileName+'_Trunk'
                bpy.ops.object.editmode_toggle()
                if merge_shared_verticies:
                    bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                bpy.ops.mesh.delete_loose()
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
                
            sprites = geometries.geometries[2]
            # add offsets to sprites vertices:
            spriteVertices = []
            for i, vertexValue in enumerate(geometries.vertexValues):
                spriteVertices.append((vertexValue[0]+ geometries.spriteVertexOffsets[i][0], vertexValue[1], vertexValue[2] + geometries.spriteVertexOffsets[i][1]))
            for j, mesh in enumerate(sprites.meshes):
                lenFaceSection = int(len(mesh.faces)/angleCnt)
#                for k in range(angleCnt):
                for k in range(1):
                    faceSection = []
                    for i_sprite in range(0,lenFaceSection,2):
                        spriteFace_1_Values = mesh.faces[k*lenFaceSection+i_sprite]
                        spriteFace_2_Values = mesh.faces[k*lenFaceSection+i_sprite+1]
                        
                        sameVertices = list(set(spriteFace_1_Values).intersection(spriteFace_2_Values))
                        diffVertices = list(set(spriteFace_1_Values).symmetric_difference(spriteFace_2_Values))
                        
                        if len(sameVertices) != 2:
                            print("Error, sprite face is not consisting of 4 vertices!!")
                            print(spriteFace_1_Values)
                            print(spriteFace_2_Values)
                            faceSection.append(spriteFace_1_Values)
                            faceSection.append(spriteFace_2_Values)
                        else:
                            spriteFace_Values = [diffVertices[0],sameVertices[0],diffVertices[1],sameVertices[1]]
                            faceSection.append(spriteFace_Values)
                    
                    # faceSection = mesh.faces[k*lenFaceSection:(k+1)*lenFaceSection]
                    
                    object = bf42_createTreeMesh(spriteVertices,faceSection, filePath, '_Sprite_'+str(j+1))
                    object.scale = (sceneScale,sceneScale,sceneScale)
                    rs_matterial = bf42_material("")
                    texture_split = mesh.textureName.split('/',1)
                    if len(texture_split) == 2:
                        rs_matterial.texture = texture_split[1]
                    rs_matterial.textureFullPath = mesh.textureName
                    rs_matterial.twosided = True
                    rs_matterial.transparent = True
                    mat = bf42_add_sm_Material(object.data, rs_matterial, fileName+'_Sprite_'+str(j+1))
                    texutre_uv_layer = object.data.uv_layers.new(name='textureMap')
                    for loop in object.data.loops:
                        texutre_uv_layer.data[loop.index].uv = (geometries.vertexTextureUV[loop.vertex_index][0],-geometries.vertexTextureUV[loop.vertex_index][1])
                    object.select_set(True)
                    bpy.context.view_layer.objects.active = object
            if len(sprites.meshes) > 0:
                bpy.ops.object.join()
                object.name = fileName+'_Sprite'
                object.data.name = fileName+'_Sprite'
                bpy.ops.object.editmode_toggle()
                if merge_shared_verticies:
                    bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                bpy.ops.mesh.delete_loose()
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
                
            billboards = geometries.geometries[3]
            for j, mesh in enumerate(billboards.meshes):
                object = bf42_createTreeMesh(geometries.vertexValues,mesh.faces, filePath, '_Billboard_'+str(j+1))
                object.scale = (sceneScale,sceneScale,sceneScale)
                texutre_uv_layer = object.data.uv_layers.new(name='textureMap')
                for loop in object.data.loops:
                    texutre_uv_layer.data[loop.index].uv = (geometries.vertexTextureUV[loop.vertex_index][0],-geometries.vertexTextureUV[loop.vertex_index][1])
            
            if fileSize != f.tell():
                print("Error, Data left at end: "+str(f.tell())+" -> "+str(fileSize)+" : "+str(fileSize-f.tell()))
            f.close()

def bf42_export_tm(directory, name, COL_object, Branch_object, Trunk_object, Sprite_object, materialID, AngleCount, applyTrans, sceneScale):
    print("########### start Export #######")
    directory = bpy.path.abspath(directory)
    if os.path.exists(directory) and name != "":
        path_tm = os.path.join(directory,name+".tm")
        with open(path_tm, "wb") as f:
            old_active_object = bpy.context.view_layer.objects.active
            
            #first calculate everything, then write it:
            allTextureNames = []
            allVertices = []
            allVertexNormals = []
            allVertexTextureUV = []
            allFaces = []
            
            #Branch and Trunk:
            Objects = [Branch_object, Trunk_object]
            for oridginalObject in Objects:
                vertices = []
                vertexNormals = []
                vertexTextureUV = []
                vertices_ref = []
                textureNames = []
                faces = []
                if oridginalObject != None:
                    object = bf42_duplicateSpecialObject(oridginalObject)
                    if applyTrans:
                        bf42_applyTransformObject(object)
                    object.data.transform(Matrix.Scale(1/sceneScale, 4))
                    bf42_triangulateObject(object)
                    mesh = object.data
                    texutre_uv_layer = None
                    for uv_layer in mesh.uv_layers:
                        if texutre_uv_layer == None:
                            texutre_uv_layer = uv_layer # use first uv_layer if no textureMap is existing
                        if uv_layer.name == "textureMap":
                            texutre_uv_layer = uv_layer
                    for materialNumber, material in enumerate(mesh.materials):
                        materialFaces = []
                        for polygon in mesh.polygons:
                            if polygon.material_index == materialNumber:
                                face = []
                                for loop_index in polygon.loop_indices:
                                    vertex_index = mesh.loops[loop_index].vertex_index
                                    vertex = mesh.vertices[vertex_index]
                                    if texutre_uv_layer == None:
                                        vertexTextureUVco = (0,0)
                                    else:
                                        vertexTextureUVco = (texutre_uv_layer.data[loop_index].uv[0],1-texutre_uv_layer.data[loop_index].uv[1])
                                    ref = (vertex.co, vertexTextureUVco)
                                    try:
                                        vertices_ref_index = vertices_ref.index(ref)
                                    except ValueError:
                                        vertices.append((vertex.co[0],vertex.co[2],vertex.co[1]))
                                        vertexNormals.append(tuple(vertex.normal))
                                        vertexTextureUV.append(vertexTextureUVco)
                                        vertices_ref.append(ref)
                                        vertices_ref_index = len(vertices_ref)-1
                                    face.append(vertices_ref_index)
                                materialFaces.append((face[0],face[2],face[1])) # correct for normal
                        if len(materialFaces) > 0:
                            faces.append(materialFaces)
                            textureNames.append("texture/"+material.BF1942_sm_Properties.texture)
                    bpy.data.objects.remove(object)
                allTextureNames.append(textureNames)
                allVertices.append(vertices)
                allVertexNormals.append(vertexNormals)
                allVertexTextureUV.append(vertexTextureUV)
                allFaces.append(faces)
            
            #Sprite:
            vertices = []
            vertexNormals = []
            vertexTextureUV = []
            spriteVertexOffsets = []
            textureNames = []
            faces = []
            spriteBoundingBox = [0]*6
            if Sprite_object != None:
                object = bf42_duplicateSpecialObject(Sprite_object)
                if applyTrans:
                    bf42_applyTransformObject(object)
                object.data.transform(Matrix.Scale(1/sceneScale, 4))
                bf42_triangulateObject(object)
                sprites = tm_sprites().loadObject(object)
                for i, material_mesh in enumerate(sprites.materialMeshes):
                    textureNames.append(material_mesh.texturename)
                    for sprite in material_mesh.sprites:
                        for v,vertexCoordinateOffset in enumerate(sprite.vertexCoordinateOffsets):
                            vertices.append(sprite.centerCoordinate)
                            vertexNormals.append((0,0,0))
                            vertexTextureUV.append(sprite.vertexTextureUV[v])
                            spriteVertexOffsets.append(vertexCoordinateOffset)
                            for k in range(3):
                                spriteBoundingBox[k] = min(spriteBoundingBox[k],sprite.centerCoordinate[k]-max(abs(vertexCoordinateOffset[0]),abs(vertexCoordinateOffset[1])))
                                spriteBoundingBox[k+3] = max(spriteBoundingBox[k+3],sprite.centerCoordinate[k]+max(abs(vertexCoordinateOffset[0]),abs(vertexCoordinateOffset[1])))
                numVertsAllMat = 0
                for i, material_mesh in enumerate(sprites.materialMeshes):
                    faces.append([])
                    for k in range(AngleCount):
                        spriteOrder = material_mesh.getOrderByAngle(k,AngleCount)
                        for sprite_i in spriteOrder:
                            numVerts = numVertsAllMat
                            for prev_sprite_i in range(sprite_i):
                                numVerts += len(material_mesh.sprites[prev_sprite_i].vertexCoordinateOffsets)
                            for face in material_mesh.sprites[sprite_i].faces:
                                faces[i].append([v+numVerts for v in face])
                    numVerts = 0
                    for sprite in material_mesh.sprites:
                        numVerts += len(sprite.vertexCoordinateOffsets)
                    numVertsAllMat += numVerts
                bpy.data.objects.remove(object)
                
                # spriteBoundingBox = getUnionBoundingBox([getBoundingBox(object.data)], spriteBoundingBox)
            allTextureNames.append(textureNames)
            allVertices.append(vertices)
            allVertexNormals.append(vertexNormals)
            allVertexTextureUV.append(vertexTextureUV)
            allFaces.append(faces)
            
            #Billboard:
            allVertices.append([])
            allFaces.append([])
            
            boundingBoxes = []
            Objects = [COL_object, Branch_object, Trunk_object]
            for Object in Objects:
                if Object != None:
                    object = bf42_duplicateSpecialObject(Object)
                    if applyTrans:
                        bf42_applyTransformObject(object)
                    object.data.transform(Matrix.Scale(1/sceneScale, 4))
                    boundingBox = getBoundingBox(object.data)
                    boundingBoxes.append(getBoundingBox(object.data))
                    bpy.data.objects.remove(object)
            
            boundingBoxes.append(spriteBoundingBox)
            boundingBox = getUnionBoundingBox(boundingBoxes)
            
            
            #header
            sm_i_w(f, 3)
            sm_i_w(f, 0)
            sm_i_w(f, AngleCount)
            sm_f_w(f, boundingBox)
            sm_f_w(f, spriteBoundingBox)
            
            #Visible meshes header
            totalNumFaces = 0
            totalNumVertices = 0
            for i, GeomFaceGroups in enumerate(allFaces):
                sm_i_w(f, len(GeomFaceGroups))
                totalNumVertices += len(allVertices[i])
                for j, faceGroup in enumerate(GeomFaceGroups):
                    numFaces = int(len(faceGroup)/(AngleCount if i in [2] else 1))
                    # will be: numFaces = int(len(faceGroup)/(AngleCount if i in [0, 2] else 1))
                    sm_i_w(f, totalNumFaces*3)
                    sm_i_w(f, numFaces)
                    totalNumFaces += numFaces*(AngleCount if i in [0, 2] else 1)
                    textureName = allTextureNames[i][j]
                    sm_i_w(f, len(textureName))
                    sm_s_w(f, textureName)
            
            #COL
            if COL_object != None:
                # materialID is None when not forced
                sm_col_export(f, COL_object, materialID, applyTrans, sceneScale)
            else:
                sm_B_w(f, (0, 0, 0, 0)) #unknown1
                
            #Visible meshes data
            sm_i_w(f, totalNumVertices)
            for i, GeomVertices in enumerate(allVertices):
                for j, vertex in enumerate(GeomVertices):
                    sm_f_w(f, vertex) # vertexValue
                    sm_f_w(f, allVertexNormals[i][j]) # vertexNormal
                    sm_i_w(f, (0x80808080 if i in [0,1] else 0)) #vertexDiffuse32, 0x80808080 for Trunk, 0 for sprite
                    sm_f_w(f, allVertexTextureUV[i][j]) # vertexTextureUV
                    sm_f_w(f, (spriteVertexOffsets[j] if i in [2] else (0,0))) # spriteVertexOffsets
            
            sm_i_w(f, totalNumFaces*3)
            totalNumVertices = 0
            for i, GeomFaceGroups in enumerate(allFaces):
                for j, faceGroup in enumerate(GeomFaceGroups):
                    for k in range(AngleCount if i in [0] else 1):
                        for face in faceGroup:
                            face_with_offset = [v+totalNumVertices for v in face]
                            sm_i_short_w(f, face_with_offset)
                totalNumVertices += len(allVertices[i])
            
            bpy.context.view_layer.objects.active = old_active_object
    else:
        print("incorrect directory of filename")










# def WriteSimpleBsp(f, obj, matIDForce):
	# bf_writeLong f numFaces
	# bf_writeLong f 0
	
	# bf_writeLong f numFaces
	# for i=1 to numFaces:
		# bf_writeFloat f ((getFaceNormal obj i).x)
		# bf_writeFloat f ((getFaceNormal obj i).z)
		# bf_writeFloat f ((getFaceNormal obj i).y)
	
		# bf_writeLong f 0
		# bf_writeLong f ((getface obj i).x - 1)
		# bf_writeLong f ((getface obj i).y - 1)
		# bf_writeLong f ((getface obj i).z - 1)
	
		# if matIDForce != -1:
			# bf_writeLong f matIDForce
		# else
			# bf_writeLong f (getFaceMatID obj i)
	
	# bf_writeString f "SimpleBSP tree method  "
	# bf_writeLong f numFaces
	
	# for i in range(numFaces):
		# bf_writeLong f i 
	
	# bf_writeShort f 0 # just filler