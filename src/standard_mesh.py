import os
import struct
import bpy
from random import random

from .misc import *

def unkownBytes(f,n):
    unknown = struct.unpack('B'*n, f.read(1*n))
#    print('unknown: {}'.format(unknown))
    return(unknown)
def sm_i(f,n=1,forceList=False):
    res = struct.unpack('L'*n, f.read(4*n))
    if n==1 and not forceList:
        return(res[0])
    return(res)
def sm_i_short(f,n=1):
    res = struct.unpack('H'*n, f.read(2*n))
    if n==1:
        return(res[0])
    return(res)
def sm_f(f,n=1):
    res = struct.unpack('f'*n, f.read(4*n))
    if n==1:
        return(res[0])
    return(res)
def sm_s(f,n=1):
    res = struct.unpack('B'*n, f.read(1*n))
    string_ret = ""
    for byte in res:
        string_ret += chr(byte)
    return(string_ret)

class sm_bsp_node:
    def __init__(self,boundingBox = None, faces = None, childeren = [None,None]):
        self.boundingBox = boundingBox
        self.faces = faces
        self.childeren = [None,None]
    def read(self,f):
        self.boundingBox = sm_f(f,6)
        facenum = sm_i(f,1)
        self.faces = sm_i(f,facenum,True)
        for child in range(2):
            hasChild = struct.unpack('B', f.read(1))[0]
            if hasChild==1:
                self.childeren[child]=sm_bsp_node().read(f)
        return(self)

class sm_header:
    def __init__(self,version = None, boundingBox = None):
        self.version = version #4 bytes, mostly 10, 9 for kits?
        self.unknown1 = (0,0,0,0) #4 bytes
        self.boundingBox = [] if boundingBox is None else boundingBox #6*4 bytes
        self.qflag = 1 #0 when Skin?, ?1 byte padding for version 10? (1 in dice&3dsmax, 0 in Metasequoia&rexman)
    def read(self,f):
        self.version = sm_i(f)
#        print('Version: {}'.format(Version))
        self.unknown1 = unkownBytes(f,4)
        if self.unknown1 != (0,0,0,0):
             print("Unexpected, sm_header.unknown1 is not 0?: "+str(self.unknown1))
        self.boundingBox = sm_f(f,6)
        if self.version==10:
            self.qflag = struct.unpack('B', f.read(1))[0]
            print("Unexpected, sm_header.qflag: "+str(self.qflag))
        elif self.version==9:
            True
        else:
            print("Error, version: "+str(self.version))
        return(self)
        

class sm_COL_mesh:
    def __init__(self):
        self.sizeOfSection = 0
        self.unknown1 = (0,0,0,0)
        self.unknown2 = 0
        self.numVertices = 0
        self.vertices = []
        self.numFaces = 0
        self.faces = []
        self.unknown3 = 0
        self.numBspEdges = 0
        self.numFaceNormals = 0
        self.faceNormals = []
        self.bsp_node_1 = None
    def read(self,f):
        self.sizeOfSection = sm_i(f)
        
        endOffset = f.tell() + self.sizeOfSection
        self.unknown1 = unkownBytes(f,4)
        if self.unknown1 != (250, 194, 151, 235):
            print("Unexpected, sm_COL_mesh.unknown1: "+str(self.unknown1))
        self.unknown2 = sm_i(f)
        if self.unknown2 != 5:
            print("Unexpected, sm_COL_mesh.unknown2: "+str(self.unknown2))
        
        self.numVertices = sm_i(f)
#        print('\tMESH_VERTICES: {}'.format(self.numVertices))
        
        for i in range(self.numVertices):
            self.vertices.append(sm_COL_vertex().read(f))
        
        self.numFaces = sm_i(f)
#        print('\tMESH_FACES: {}'.format(self.numFaces))
        for i in range(self.numFaces):
            self.faces.append(sm_COL_face().read(f))
        
        self.unknown3 = sm_i(f) # something to do with the faceCount and the dimension of the bsp tree.
        # or maybe: The diameter of the communication network, or at least the length of the longest path that allows state to 
        # be moved from one processor to another clearly imposes a lower bound on l....
        self.numBspEdges = sm_i(f)
        
        self.numFaceNormals = sm_i(f)
#        print('\tFACENORMAL_COUNT: {}'.format(self.numFaceNormals))
        # print("\t?: {} <-> {} {} {}".format(self.unknown3, self.numVertices, self.numFaces, self.numFaceNormals))
        for i in range(self.numFaceNormals):
            self.faceNormals.append(sm_COL_faceNormal().read(f))
            
            #debug check:
            faceNormal = self.faceNormals[i]
            if(faceNormal.unknown[0] != 0 or faceNormal.unknown[1:4] != self.faces[i].vertices or faceNormal.unknown[4] != self.faces[i].materialID):
                print("Unexpected: sm_COL_mesh_faceNormal.unknown = "+str(faceNormal.unknown))
                print("   - : "+str(self.faces[i].vertices)+", "+str(self.faces[i].materialID))
        print(f.tell())
        self.bsp_node_1 = sm_bsp_node().read(f)
        print(f.tell())
        return(self)

class sm_COL_vertex:
    def __init__(self,vertex = (0,0,0), unknown=0):
        self.vertex = vertex
        self.unknown = unknown #mat id? VertMod?
    def read(self,f):
        self.vertex = sm_f(f,3)
        self.unknown = struct.unpack('B'*2, f.read(1*2))
        f.read(2) # allignmet (last 2 bytes of vertex[0] Repeated)
        return(self)

class sm_COL_face:
    def __init__(self,vertices = (0,0,0), materialID=0):
        self.vertices = vertices
        self.materialID = materialID
    def read(self,f):
        self.vertices = sm_i_short(f,3)
        self.materialID = sm_i_short(f)
        return(self)

class sm_COL_faceNormal:
    def __init__(self,vertex = (0,0,0), unknown=(0,0,0,0,0)):
        self.vertex = vertex
        self.unknown = unknown #seems to be: (0, sm_COL_face.vertices, sm_COL_face.materialID)
    def read(self,f):
        self.vertex = sm_f(f,3)
        self.unknown = sm_i(f,5)
        return(self)
        
class sm_LOD_mesh:
    def __init__(self,numMaterials = 0,materials = None):
        self.numMaterials = numMaterials
        self.materials = materials if materials is not None else []
    def read(self,f):
        self.numMaterials = sm_i(f)
        for i in range(self.numMaterials):
            self.materials.append(sm_LOD_mesh_material().read_1(f))
        for i in range(self.numMaterials):
            self.materials[i].read_2(f)
        return(self)

class sm_LOD_mesh_material:
    def __init__(self,name = "", vertexValues=None, vertexNormals=None, vertexTextureUV=None, vertexLightmapUV=None, faces=None):
        self.name = name
        self.unknown = (0,0,0,0,0,0,0,0,0,0,0,0) #12 bytes
        self.renderType = 0
        self.vertexFormat = 0
        self.vertexByteSize = 0
        self.numVertices = 0
        self.numFaces = 0
        self.materialSettings = 0 # mostly 0:,4 for windows depthwrite, and iv seen 2 for Kit_AlliesAssault_m1_Material1/Yak9_hull_m1_Material1/Willy_Hul_M1_Material2
        # probably bit 2 is for transparent enable, and bit 3 is for depthwrite enable
        # bit 2 is not required as far as I know, bit 3 is required to achieve depthwrite
        
        self.vertexValues = [] if vertexValues is None else vertexValues
        self.vertexNormals = [] if vertexNormals is None else vertexNormals
        self.vertexTextureUV = [] if vertexTextureUV is None else vertexTextureUV
        self.vertexLightmapUV = [] if vertexLightmapUV is None else vertexLightmapUV
        self.faceValues = []
        
        #not in sm (generated in read_2())
        self.faces = [] if faces is None else faces
    def read_1(self,f):
        nameLn = sm_i(f)
        self.name = (sm_s(f,nameLn))
        self.unknown = unkownBytes(f,12) # all 0?
        
        #for debugging:
        if self.unknown != (0,0,0,0,0,0,0,0,0,0,0,0):
             print("Unexpected, Material_unknown is not 0?: "+str(self.unknown))
        
        self.renderType = sm_i(f)
        self.vertexFormat = sm_i(f)
        self.vertexByteSize = sm_i(f)
        self.numVertices = sm_i(f)
        self.numFaces = sm_i(f)
        
        self.materialSettings = sm_i(f)
        #for debugging:
        if not self.materialSettings in [0,2,4]:
             print("Error, materialSettings is : "+str(self.materialSettings)+"? - "+self.name+" at "+str(f.tell()))
        if not self.vertexFormat in [1041,9233]: #[reg, lightmap]
            print("Error, vertexFormat is:"+str(self.vertexFormat))
        if not self.renderType in [4,5]:
            print("Error, renderType is:"+str(self.renderType))
        if  not self.vertexByteSize in [32,40]: #64?
            print("Error, vertexByteSize is:"+str(self.vertexByteSize))
        return(self)
    def read_2(self,f):
        hasLightmap = self.vertexByteSize in [40]
        for Vert_number in range(self.numVertices):
            
            realVert = sm_f(f,3)
            self.vertexValues.append((realVert[0],realVert[2],realVert[1]))
            
            Vnormal = sm_f(f,3)
            self.vertexNormals.append((Vnormal[0],Vnormal[2],Vnormal[1]))
            
            if not hasLightmap:
                self.vertexTextureUV.append(sm_f(f,2))
            else:
                self.vertexTextureUV.append(sm_f(f,2))
                self.vertexLightmapUV.append(sm_f(f,2))
        self.faceValues = sm_i_short(f,self.numFaces)
        
        if self.renderType == 5: # "TriangleStrip"
            for i in range(0,self.numFaces-2):
                self.faces.append((self.faceValues[i],self.faceValues[i+1],self.faceValues[i+2]))
        else: #"TriangleList"
            for i in range(0,self.numFaces,3):	
                self.faces.append((self.faceValues[i+2],self.faceValues[i+1],self.faceValues[i]))
        return(self)
#############################################################

def bf42_add_sm_Material(mesh, rs_matterial, name="bf1942_Material"):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = random(), random(), random(), 1
    mat.use_nodes = True;
    
    mat.BF1942_sm_Properties.texture = rs_matterial.texture
    mat.BF1942_sm_Properties.customTexturePath = rs_matterial.textureFullPath
    mat.BF1942_sm_Properties.transparent = rs_matterial.transparent
    mat.BF1942_sm_Properties.lighting = rs_matterial.lighting
    mat.BF1942_sm_Properties.lightingSpecular = rs_matterial.lightingSpecular
    mat.BF1942_sm_Properties.twosided = rs_matterial.twosided
    mat.BF1942_sm_Properties.envmap = rs_matterial.envmap
    mat.BF1942_sm_Properties.textureFade = rs_matterial.textureFade
    mat.BF1942_sm_Properties.depthWrite = rs_matterial.depthWrite
    mat.BF1942_sm_Properties.blendSrc = rs_matterial.blendSrc
    mat.BF1942_sm_Properties.blendDest = rs_matterial.blendDest
    mat.BF1942_sm_Properties.alphaTestRef = rs_matterial.alphaTestRef
    mat.BF1942_sm_Properties.materialDiffuse = rs_matterial.materialDiffuse
    mat.BF1942_sm_Properties.materialSpecular = rs_matterial.materialSpecular
    mat.BF1942_sm_Properties.materialSpecularPower = rs_matterial.materialSpecularPower
    if rs_matterial.transparent:
        mat.blend_method = 'BLEND'
    if rs_matterial.textureFade:
        mat.blend_method = 'BLEND'
    mat.use_backface_culling = not rs_matterial.twosided

    nodes = mat.node_tree.nodes
    node_output = nodes.get("Material Output")
    node_principled = nodes.get("Principled BSDF")
#    node_diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
    node_texture = nodes.new(type="ShaderNodeTexImage")
    node_texture.location = (-335, 215.0)
    node_UVMap_texture = nodes.new(type="ShaderNodeUVMap")
    node_UVMap_texture.location = (-530, 60)
    node_UVMap_texture.uv_map = "textureMap"
    links = mat.node_tree.links
    FILE_PATH = bf42_getTexturePathByName(rs_matterial.texture)
    if FILE_PATH != False:
        image = bpy.data.images.load(FILE_PATH, check_existing=False)
        node_texture.image = image
        new_link = links.new(node_texture.outputs[1],node_principled.inputs[18])
    else:
        print("texture not found")
    new_link = links.new(node_UVMap_texture.outputs[0],node_texture.inputs[0])
    new_link = links.new(node_texture.outputs[0],node_principled.inputs[0])
    mesh.materials.append(mat)
    return(mat)
    
class bf42_materials:
    def __init__(self):
        self.material_list = []
    def read_rs_file(self, path):
        property_names = ["texture", "transparent", "lighting", "lightingSpecular", "twosided", "envmap", "textureFade", "depthWrite",
                        "blendSrc", "blendDest", "alphaTestRef", "materialDiffuse", "materialSpecular", "materialSpecularPower"]
        blend_modes = ["sourceAlphaSat", "invDestAlpha", "destAlpha", "invDestColor", "destColor",
                        "invSourceAlpha", "sourceAlpha", "invSourceColor", "sourceColor", "one", "zero"]
        path = bpy.path.abspath(path)
        try:
            f = open(path, 'r', encoding="utf8", errors="surrogateescape")
        except IOError:
            print("File not accessible")
        else:
            fileStr = f.read()
            pointer = 0;
            while not fileStr.find("subshader",pointer)==-1:
                pointer = fileStr.find("subshader",pointer)
                pointer = fileStr.find('"',pointer)
                if pointer == -1: break
                end = fileStr.find('"',pointer+1)
                if end == -1: break
                name=fileStr[pointer+1: end]
                material = bf42_material(name)
                pointer = fileStr.find('"',end)
                if pointer == -1: break
                pointer = fileStr.find('"',pointer+1)
                if pointer == -1: break
                start = fileStr.find('{',pointer)
                if start == -1: break
                pointer = fileStr.find('}',start)
                if pointer == -1: break
                properties_raw=fileStr[start+1: pointer].strip().split(';')
                properties = []
                for property in properties_raw:
                    property = property.strip()
                    property_split=property.split(' ',1)
                    if len(property_split) == 2:
                        property_name = property_split[0]
                        property_value = property_split[1].strip()
                        if property_name in property_names:
                            if property_name in["transparent", "lighting", "lightingSpecular", "twosided", "envmap", "textureFade", "depthWrite"]:
                                if property_value.lower() == "true":
                                    material.__setattr__(property_name, True)
                                elif property_value.lower() == "false":
                                    material.__setattr__(property_name, False)
                            elif property_name in["blendSrc", "blendDest"]:
                                for blend_mode in blend_modes:
                                    if property_value.lower() == blend_mode.lower():
                                        material.__setattr__(property_name, blend_mode)
                                        break
                            elif property_name in["alphaTestRef", "materialSpecularPower"]:
                                if bf42_isFloat(property_value): 
                                    property_value = float(property_value)
                                    material.__setattr__(property_name, property_value)
                            elif property_name in ["materialDiffuse", "materialSpecular"]:
                                property_values = property_value.split(" ")
                                if len(property_values) == 3:
                                    property_value_list = []
                                    for property_value_sub in property_values:
                                        if bf42_isFloat(property_value_sub.strip()):
                                            property_value_sub = float(property_value_sub.strip())
                                            property_value_list.append(property_value_sub)
                                    if len(property_value_list) == 3:
                                        material.__setattr__(property_name, property_value_list)
                            elif property_name == "texture":
                                texture_split = property_value.split('/',1)
                                if len(texture_split) == 2:
                                    material.texture = texture_split[1][0:-1]
                                material.textureFullPath = property_value[1:-1]
                            else:
                                material.__setattr__(property_name, property_value)
                self.material_list.append(material)
    
    def get_material(self, name):
        for material in self.material_list:
            if material.name.lower() == name.lower():
                return(material)
        return(False)
class bf42_material:
    def __init__(self,name):
        self.name = name
        self.texture = ""
        self.textureFullPath = ""
        self.transparent = False
        self.lighting = True
        self.lightingSpecular = False
        self.twosided = False
        self.envmap = False
        self.textureFade = False
        self.depthWrite = True
        self.blendSrc = "invSourceAlpha"
        self.blendDest = "sourceAlpha"
        self.alphaTestRef = 0 # or mabye 0.5
        self.materialDiffuse = (1,1,1)
        self.materialSpecular = (1,1,1)
        self.materialSpecularPower = 20

###############################################################        
def remake_sm_BSP(path,depth='-a'):
#    print(__file__)
    addonPath = bpy.utils.user_resource('SCRIPTS', "addons")+"/BF1942 addon/"
    cmd = '"'+addonPath+'bin/makeBSP.exe" "'+path+'" '+depth+''
    p = os.popen(cmd)
#    print(os.popen(cmd).read())
    p.close()
###############################################################  
def bf42_import_sm_debug(path):
    weird_stuff=[]
    print("")
    print(".SM structure")
    try:
        f = open(path, 'rb')
    except IOError:
        print("File not accessible")
    else:
        f.seek(0,2)
        fileSize = f.tell()
        f.seek(0)
        
        header = sm_header().read(f)
        print(header.version)
        numCollisionMeshes = sm_i(f)
#        print('COLLISION_COUNT: {}'.format(numTopModels))
        
        for collisionMeshNumber in range(numCollisionMeshes):
            startOffset = f.tell()
            print('COL_{}'.format(collisionMeshNumber))
            collisionMesh = sm_COL_mesh().read(f)
            bsp_node = collisionMesh.bsp_node_1
            print(count_nodes(bsp_node))
            print(count_nodeFaces(bsp_node))
            endOffset = startOffset+4+collisionMesh.sizeOfSection
            
            if endOffset != f.tell():
                print("\tError!!!!!")
                print('\t{} != {}'.format(f.tell(),endOffset))
                f.seek(endOffset) 
        
        
        numLods = sm_i(f)
#        print('LOD_COUNT: {}'.format(numLodMeshes))
        for LodNumber in range(numLods):
            print('LOD_{}'.format(LodNumber))
            LOD_mesh = sm_LOD_mesh().read(f)
#            for material in LOD_mesh.materials:
#                print(material.materialName)
#                print(material.numFaces)
        
        hasShadowLods = sm_i(f)
        if hasShadowLods == 1:
            numShadowLods = sm_i(f) # 1 seems to be for number of ShadowLods, is it always 1?
            for ShadowLodNumber in range(numShadowLods):
                print('SHADOW_LOD_{}'.format(ShadowLodNumber))
                LOD_mesh = sm_LOD_mesh().read(f)
#                for material in LOD_mesh.materials:
#                    print(material.materialName)
#                    print(material.numFaces)
        
        PortalMeshBlockSize = sm_i(f)
        if PortalMeshBlockSize != 0:
            print(PortalMeshBlockSize)
            vertices = []
            faces = []
            unknown1 = unkownBytes(f,4)
            if unknown1 != (252, 194, 195, 153):
                print("Unexpected, sm_COL_mesh.unknown1: "+str(unknown1))
            unknown2 = sm_i(f)
            if unknown2 != 3:
                print("Unexpected, sm_COL_mesh.unknown2: "+str(unknown2))
#            print(sm_i(f,2))
            numVertices = sm_i(f)
            numFaces = sm_i(f)
            print("numVertices = "+str(numVertices)+", numFaces = "+str(numFaces))
            print(sm_f(f,numVertices*24))
            iets = sm_i_short(f)
            print(sm_i_short(f,iets))
            print(sm_i_short(f,4))
#        numVertices = sm_i(f)
#        print('\tMESH_VERTICES: {}'.format(numVertices))
#        numFaces = sm_i(f)
#        print('\tMESH_FACES: {}'.format(numFaces))
        
#        for i in range(numVertices):
#            vertices.append(sm_COL_vertex().read(f))
#            print(sm_f(f,3))
#            print(unkownBytes(f,4*3))
#            print(unkownBytes(f,4))
#        print(sm_i_short(f,100))
#        for vertex in vertices:
#            print(vertex.vertex)
#        
#        numFaces = sm_i(f)
#        print('\tMESH_FACES: {}'.format(numFaces))
#        for i in range(numFaces):
#            faces.append(sm_COL_face().read(f))

        
        
        
#        PortalMeshBlockSize = sm_i(f)
        # 252, 194, 195, 153, 4, 0, 0, 0 - Metasequoia
        # 252, 194, 195, 153, 3, 0, 0, 0 - Dice
#        print(unkownBytes(f,PortalMeshBlockSize))
        
        if fileSize != f.tell():
            print("Error, Data left at end: "+str(f.tell())+" -> "+str(fileSize)+" : "+str(fileSize-f.tell()))
        f.close()

def bf42_import_sm(path, add_BoundingBox, add_Collision, add_Visible, add_only_main_LOD, merge_shared_verticies,sceneScale):
    messagesWarn = []
    path = bpy.path.abspath(path)
    basename = bpy.path.basename(path).split('.',1)[0]
    fileName = basename.split('.',1)[0]
    directory = os.path.dirname(path)
    path_rs = os.path.join(directory,fileName+".rs")
    path_sm = os.path.join(directory,fileName+".sm")

    print(fileName)

    rs_materials = bf42_materials()
    rs_materials.read_rs_file(path_rs)
    
    try:
        f = open(path_sm, 'rb')
    except IOError:
        print("File not accessible")
    else:
        f.seek(0,2)
        fileSize = f.tell()
        f.seek(0)
        
        header = sm_header().read(f)
        if add_BoundingBox:
            BB = header.boundingBox
            vertices = [(BB[0],BB[2],BB[1]),(BB[0],BB[5],BB[1]),(BB[3],BB[5],BB[1]),(BB[3],BB[2],BB[1]),
                        (BB[0],BB[2],BB[4]),(BB[0],BB[5],BB[4]),(BB[3],BB[5],BB[4]),(BB[3],BB[2],BB[4])]
            edges = [(0,1),(1,2),(2,3),(3,0),
                    (4,5),(5,6),(6,7),(7,4),
                    (0,4),(1,5),(2,6),(3,7),]
            BoundingBox_object = bf42_createObject(vertices,[], fileName+'_BoundingBox',edges = edges)
            BoundingBox_object.scale = (sceneScale,sceneScale,sceneScale)
        numCollisionMeshes = sm_i(f)
#        print('COLLISION_COUNT: {}'.format(numTopModels))
        
        for collisionMeshNumber in range(numCollisionMeshes):
            startOffset = f.tell()
            print('COL_{}'.format(collisionMeshNumber))
            collisionMesh = sm_COL_mesh().read(f)
            vertices = []
            faces = []
            for vertex in collisionMesh.vertices:
                vertices.append((vertex.vertex[0],vertex.vertex[2],vertex.vertex[1]))
            for face in collisionMesh.faces:
                faces.append(face.vertices)
                #ToDo: face material
            if add_Collision:
                object = bf42_createObject(vertices,faces, fileName+'_COL'+str(collisionMeshNumber))
                object.scale = (sceneScale,sceneScale,sceneScale)
            endOffset = startOffset+4+collisionMesh.sizeOfSection
            
            if endOffset != f.tell():
                print("\tError!!!!!")
                print('\t{} != {}'.format(f.tell(),endOffset))
                f.seek(endOffset) 
        
        
        numLods = sm_i(f)
        numLodsToPars = numLods
        if add_only_main_LOD: numLodsToPars = 1
        if not add_Visible: numLodsToPars = 0
        for LodNumber in range(numLodsToPars):
            print('LOD_{}'.format(LodNumber))
            bpy.ops.object.select_all(action='DESELECT')
            LOD_mesh = sm_LOD_mesh().read(f)
            for materialNumber, material in enumerate(LOD_mesh.materials):
                rs_matterial = rs_materials.get_material(material.name)
                if rs_matterial == False:
                    rs_matterial = bf42_material(material.name)
                # ToDo: add vertexNormals
                object = bf42_createObject(material.vertexValues,material.faces, fileName+'_LOD'+str(LodNumber)+'_Material'+str(materialNumber))
                object.scale = (sceneScale,sceneScale,sceneScale)
                mesh = object.data
                texutre_uv_layer = mesh.uv_layers.new(name='textureMap')
                light_uv_layer = mesh.uv_layers.new(name='lightMap')
                mat = bf42_add_sm_Material(mesh, rs_matterial, material.name)
                for loop in object.data.loops:
                    texutre_uv_layer.data[loop.index].uv = (material.vertexTextureUV[loop.vertex_index][0],1-material.vertexTextureUV[loop.vertex_index][1])
                    if material.vertexByteSize in [40]:
                        light_uv_layer.data[loop.index].uv = (material.vertexLightmapUV[loop.vertex_index][0],1-material.vertexLightmapUV[loop.vertex_index][1])
                object.select_set(True)
                bpy.context.view_layer.objects.active = object
            if len(LOD_mesh.materials) > 0:
                bpy.ops.object.join()
                object.name = fileName+'_LOD'+str(LodNumber)
                object.data.name = fileName+'_LOD'+str(LodNumber)
                if merge_shared_verticies:
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                    bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
        #skip through rest of lods:
        for LodNumber in range(numLods-numLodsToPars):
            sm_LOD_mesh().read(f)
        
        if f.tell() < fileSize: # fix for 'broken' meshes that have EOF after LODs
            hasShadowLods = sm_i(f)
            if hasShadowLods == 1:
                numShadowLods = sm_i(f) # 1 seems to be for number of ShadowLods, is it always 1?
                for ShadowLodNumber in range(numShadowLods):
                    print('SHADOW_LOD_{}'.format(ShadowLodNumber))
                    LOD_mesh = sm_LOD_mesh().read(f)
                    for materialNumber, material in enumerate(LOD_mesh.materials):
                        object = bf42_createObject(material.vertexValues,material.faces, fileName+'_SHADOW_LOD')
                        object.scale = (sceneScale,sceneScale,sceneScale)
            f.close()


#some BSP debugging:
def count_nodes(node):
    count = 1
    child1 = node.childeren[0]
    child2 = node.childeren[1]
    if child1 is not None:
        count += count_nodes(child1)
    if child2 is not None:
        count += count_nodes(child2)
    return(count)
def count_nodeFaces(node,depth=0):
#    for i in range(depth):
#        print(' ',end='')
#    print(len(node.faces))
    count = len(node.faces)
    child1 = node.childeren[0]
    child2 = node.childeren[1]
    if child1 is not None:
#        for i in range(depth):
#            print(' ',end='')
#        print('1')
        count += count_nodeFaces(child1,depth+1)
    if child2 is not None:
#        for i in range(depth):
#            print(' ',end='')
#        print('2')
        count += count_nodeFaces(child2,depth+1)
    return(count)


#missing atm:
#PortalMesh

#a0 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::load(dice::ref2::io::IStream *)
#a4 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadHeader(dice::ref2::io::IStream *)
#a8 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadCollision(dice::ref2::io::IStream *)
#ac dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadLods(dice::ref2::io::IStream *)
#b0 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadLod(dice::ref2::io::IStream *,std::vector<dice::ref2::geom::StandardMeshBlock,std::allocator<dice::ref2::geom::StandardMeshBlock>> &,uint)
#b4 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadShadowLods(dice::ref2::io::IStream *)
#b8 dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadShadowLod(dice::ref2::io::IStream *,std::vector<dice::ref2::geom::StandardMeshBlock,std::allocator<dice::ref2::geom::StandardMeshBlock>> &,uint)
#bc dice::ref2::geom::BStandardMeshTemplate<dice::ref2::geom::IStandardMeshTemplate,dice::ref2::geom::StandardMesh,dice::ref2::geom::StandardMeshBlock>::loadPortalMesh(dice::ref2::io::IStream *)