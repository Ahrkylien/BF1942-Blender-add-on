import os
import struct
import bpy
from random import random
from mathutils import Matrix

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
    
def sm_i_w(f, val):
    if not isinstance(val, (list,tuple)): val = [val]
    return(f.write(struct.pack('L'*len(val), *val)))
def sm_i_short_w(f, val):
    if not isinstance(val, (list,tuple)): val = [val]
    return(f.write(struct.pack('H'*len(val), *val)))
def sm_f_w(f, val):
    if not isinstance(val, (list,tuple)): val = [val]
    return(f.write(struct.pack('f'*len(val), *val)))
def sm_s_w(f, val):
    return(f.write(bytearray(val.encode())))
def sm_B_w(f, val):
    if not isinstance(val, (list,tuple)): val = [val]
    return(f.write(struct.pack('B'*len(val), *val)))
    

class sm_bsp_node:
    def __init__(self,boundingBox = None, faces = None, childeren = [None,None]):
        self.boundingBox = boundingBox
        self.facenum = 0
        self.faces = faces
        self.childeren = [None,None]
    def read(self,f):
        self.boundingBox = sm_f(f,6)
        self.facenum = sm_i(f,1)
        self.faces = sm_i(f,self.facenum,True)
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
        self.unknown1 = (250, 194, 151, 235)
        self.unknown2 = 5
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
        self.materials = [] if materials is None else materials
    def read(self,f):
        self.numMaterials = sm_i(f)
        for i in range(self.numMaterials):
            self.materials.append(sm_LOD_mesh_material().read_1(f))
        for i in range(self.numMaterials):
            self.materials[i].read_2(f)
        return(self)

class sm_LOD_mesh_material:
    def __init__(self,name = "", materialSettings=0, vertexValues=None, vertexNormals=None, vertexTextureUV=None, vertexLightmapUV=None, faces=None):
        self.nameLen = len(name)
        self.name = name
        self.unknown = (0,0,0,0,0,0,0,0,0,0,0,0) #12 bytes
        self.renderType = 4
        self.vertexFormat = 1041 if vertexLightmapUV == None else 9233
        self.vertexByteSize = 32 if vertexLightmapUV == None else 40
        self.numVertices = len(vertexValues) if vertexValues != None else 0
        self.numFaceValues = (len(faces) if faces != None else 0)*3
        self.materialSettings = materialSettings # mostly 0:,4 for windows depthwrite, and iv seen 2 for Kit_AlliesAssault_m1_Material1/Yak9_hull_m1_Material1/Willy_Hul_M1_Material2
        # probably bit 2 is for transparent enable, and bit 3 is for depthwrite enable
        # bit 2 is not required as far as I know, bit 3 is required to achieve depthwrite
        
        self.vertexValues = [] if vertexValues is None else vertexValues
        self.vertexNormals = [] if vertexNormals is None else vertexNormals
        self.vertexTextureUV = [] if vertexTextureUV is None else vertexTextureUV
        self.vertexLightmapUV = [] if vertexLightmapUV is None else vertexLightmapUV
        self.faceValues = []
        
        #not in sm (generated in read_2())
        self.faces = [] if faces is None else faces
        for face in self.faces:
            self.faceValues.append(face[0])
            self.faceValues.append(face[1])
            self.faceValues.append(face[2])
    def read_1(self,f):
        self.nameLen = sm_i(f)
        self.name = (sm_s(f,self.nameLen))
        self.unknown = unkownBytes(f,12) # all 0?
        
        #for debugging:
        if self.unknown != (0,0,0,0,0,0,0,0,0,0,0,0):
             print("Unexpected, Material_unknown is not 0?: "+str(self.unknown))
        
        self.renderType = sm_i(f)
        self.vertexFormat = sm_i(f)
        self.vertexByteSize = sm_i(f)
        self.numVertices = sm_i(f)
        self.numFaceValues = sm_i(f)
        
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
            
            self.vertexTextureUV.append(sm_f(f,2))
            
            if hasLightmap:
                self.vertexLightmapUV.append(sm_f(f,2))
        self.faceValues = sm_i_short(f,self.numFaceValues)
        
        if self.renderType == 5: # "TriangleStrip"
            for i in range(0,self.numFaceValues-2):
                self.faces.append((self.faceValues[i],self.faceValues[i+1],self.faceValues[i+2]))
        else: #"TriangleList"
            for i in range(0,self.numFaceValues,3):	
                self.faces.append((self.faceValues[i+2],self.faceValues[i+1],self.faceValues[i]))
        return(self)
    def write_1(self,f):
        sm_i_w(f,self.nameLen)
        sm_s_w(f,self.name)
        sm_B_w(f,self.unknown)
        sm_i_w(f,self.renderType)
        sm_i_w(f,self.vertexFormat)
        sm_i_w(f,self.vertexByteSize)
        sm_i_w(f,self.numVertices)
        sm_i_w(f,self.numFaceValues)
        sm_i_w(f,self.materialSettings)
        return(self)
    def write_2(self,f):
        hasLightmap = self.vertexByteSize in [40]
        for vertexNumber, vertexValue in enumerate(self.vertexValues):
            sm_f_w(f,vertexValue)
            sm_f_w(f,self.vertexNormals[vertexNumber])
            sm_f_w(f,self.vertexTextureUV[vertexNumber])
            if hasLightmap:
                sm_f_w(f,self.vertexLightmapUV[vertexNumber])
        sm_i_short_w(f,self.faceValues)
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

def bool2str(bool):
    return("true" if bool else "false")
def list2str(list):
    return(str(list[0])+" "+str(list[1])+" "+str(list[2]))
def write_rs_file(path,RS_materials):
    defaultMat = bf42_material("tmp");
    with open(path, "w") as f:
        for matNR, mat in enumerate(RS_materials):
            f.write("subshader \"material_"+str(matNR)+"\" \"StandardMesh/Default\"\n{\n")
            if mat.texture != "":
                f.write("\ttexture \"texture/"+mat.texture+"\";\n")
            if mat.transparent != defaultMat.transparent:
                f.write("\ttransparent "+bool2str(mat.transparent)+";\n")
            if mat.lighting != defaultMat.lighting:
                f.write("\tlighting "+bool2str(mat.lighting)+";\n")
            if mat.lightingSpecular != defaultMat.lightingSpecular:
                f.write("\tlightingSpecular "+bool2str(mat.lightingSpecular)+";\n")
            if mat.twosided != defaultMat.twosided:
                f.write("\ttwosided "+bool2str(mat.twosided)+";\n")
            if mat.envmap != defaultMat.envmap:
                f.write("\tenvmap "+bool2str(mat.envmap)+";\n")
            if mat.textureFade != defaultMat.textureFade:
                f.write("\ttextureFade "+bool2str(mat.textureFade)+";\n")
            if mat.depthWrite != defaultMat.depthWrite:
                f.write("\tdepthWrite "+bool2str(mat.depthWrite)+";\n")
            if mat.blendSrc != defaultMat.blendSrc:
                f.write("\tblendSrc "+mat.blendSrc+";\n")
            if mat.blendDest != defaultMat.blendDest:
                f.write("\tblendDest "+mat.blendDest+";\n")
            if mat.alphaTestRef != defaultMat.alphaTestRef:
                f.write("\talphaTestRef "+str(mat.alphaTestRef)+";\n")
            if mat.materialDiffuse != defaultMat.materialDiffuse:
                f.write("\tmaterialDiffuse "+list2str(mat.materialDiffuse)+";\n")
            if mat.materialSpecular != defaultMat.materialSpecular:
                f.write("\tmaterialSpecular "+list2str(mat.materialSpecular)+";\n")
            if mat.materialSpecularPower != defaultMat.materialSpecularPower:
                f.write("\tmaterialSpecularPower "+str(mat.materialSpecularPower)+";\n")
            f.write("}\n\n")

def bf42_addMaterialID_Material(mesh, materialID):
    materialName = "bf42_materialID_"+str(materialID)
    mat = None
    for material in bpy.data.materials:
        if material.name == materialName:
            if material.BF1942_sm_Properties.MaterialID == materialID:
                mat = material
            else:
                material.name = materialName+"_ERROR"
            break
    if mat == None:
        mat = bpy.data.materials.new(materialName)
        mat.diffuse_color = random(), random(), random(), 1
        mat.BF1942_sm_Properties.MaterialID = materialID
    mesh.materials.append(mat)
    return(mat)
###############################################################        
def remake_sm_BSP(path,depth='-a'):
    BSP_path = os.path.normpath(os.path.join(__file__,"../../bin/makeBSP.exe"))
    cmd = '"'+BSP_path+'" "'+path+'" '+depth+''
#    print(cmd)
    p = os.popen(cmd)
#    print(p.read())
    p.close()

def getBoundingBox(mesh):
    bb = [0,0,0,0,0,0]
    firstIteration = True
    for polygon in mesh.polygons:
        for vertex_index in polygon.vertices:
            v = mesh.vertices[vertex_index].co
            if firstIteration:
                bb[0] = v[0]
                bb[1] = v[2]
                bb[2] = v[1]
                bb[3] = v[0]
                bb[4] = v[2]
                bb[5] = v[1]
                firstIteration = False
            else:
                bb[0] = min(bb[0],v[0])
                bb[1] = min(bb[1],v[2])
                bb[2] = min(bb[2],v[1])
                bb[3] = max(bb[3],v[0])
                bb[4] = max(bb[4],v[2])
                bb[5] = max(bb[5],v[1])
    return(bb)

def sm_col_export(f, object, materialID, applyTrans, sceneScale):
    object = bf42_duplicateSpecialObject(object)
    if applyTrans:
        bf42_applyTransformObject(object)
    object.data.transform(Matrix.Scale(1/sceneScale, 4))
    bf42_triangulateObject(object)
    mesh = object.data
    
    startOfSection = f.tell()
    sm_i_w(f, 0) #sizeOfSection
    sm_B_w(f, (250, 194, 151, 235)) #unknown1
    sm_i_w(f, 5) #unknown2
    
    faces = []
    faces_materialID = []
    faceNormals = []
    vertices = []
    verticesMaterial = []
    vertex_indeces = []
    for polygon in mesh.polygons:
        face = []
        faceNormals.append(tuple(polygon.normal))
        material_index = polygon.material_index
        if len(mesh.materials) > material_index:
            materialID_face = mesh.materials[material_index].BF1942_sm_Properties.MaterialID
        else:
            materialID_face = 0
        faces_materialID.append(materialID_face)
        for vertex_index in polygon.vertices:
            if not vertex_index in vertex_indeces:
                vertices.append(tuple(mesh.vertices[vertex_index].co))
                verticesMaterial.append(materialID_face)
                vertex_indeces.append(vertex_index)
            face.append(vertex_indeces.index(vertex_index))
        faces.append(tuple(face))
    sm_i_w(f, len(vertices)) #numVertices
    for vertexNumber, vertex in enumerate(vertices):
        sm_f_w(f, (vertex[0],vertex[2],vertex[1]))
        sm_i_short_w(f, verticesMaterial[vertexNumber])
        sm_i_short_w(f, 0)
    sm_i_w(f, len(faces)) #numFaces
    for faceNumber, face in enumerate(faces):
        sm_i_short_w(f, (face[0],face[1],face[2]))
        face_materialID = materialID if materialID != None else faces_materialID[faceNumber]
        sm_i_short_w(f, face_materialID) #materialID
    sm_i_w(f, len(faces)) #unknown3
    sm_i_w(f, 0) #numBspEdges
    sm_i_w(f, len(faceNormals)) #numFaceNormals
    for faceNumber, faceNormal in enumerate(faceNormals):
        sm_f_w(f, faceNormal)
        vertex = faces[faceNumber]
        face_materialID = materialID if materialID != None else faces_materialID[faceNumber]
        sm_i_w(f, (0,vertex[0],vertex[1],vertex[2],face_materialID)) #(0, sm_COL_face.vertices, sm_COL_face.materialID)
    
    boundingBox = getBoundingBox(mesh)
    sm_f_w(f, boundingBox) #boundingBox
    sm_i_w(f, len(faces)) #facenum
    for faceNumber, face in enumerate(faces):
        sm_i_w(f,faceNumber)
    sm_B_w(f,(0,0)) #childeren
    
    sizeOfSection = f.tell()-startOfSection-4
    f.seek(startOfSection)
    sm_i_w(f, sizeOfSection) #sizeOfSection
    f.seek(0,2)
    
    bpy.data.objects.remove(object)

def sm_LOD_export(f, object, applyTrans, sceneScale, addLightMapUV=False):
    object = bf42_duplicateSpecialObject(object)
    if applyTrans:
        bf42_applyTransformObject(object)
    object.data.transform(Matrix.Scale(1/sceneScale, 4))
    bf42_triangulateObject(object)
    mesh = object.data
    
    RS_materials = []
    
    texutre_uv_layer = None
    light_uv_layer = None
    for uv_layer in mesh.uv_layers:
        if texutre_uv_layer == None:
            texutre_uv_layer = uv_layer # use first uv_layer if no textureMap is existing
        if uv_layer.name == "textureMap":
            texutre_uv_layer = uv_layer
        if uv_layer.name == "lightMap":
            light_uv_layer = uv_layer
    if light_uv_layer == None and addLightMapUV: # generate lightMapUV
        light_uv_layer = mesh.uv_layers.new(name='lightMap')
        light_uv_layer.active = True
        bpy.ops.object.select_all(action='DESELECT')
        object.select_set(True)
        bpy.ops.uv.lightmap_pack(PREF_CONTEXT='ALL_FACES', PREF_PACK_IN_ONE=True, PREF_NEW_UVLAYER=False, PREF_APPLY_IMAGE=False, PREF_IMG_PX_SIZE=128, PREF_BOX_DIV=12, PREF_MARGIN_DIV=0.5) 
    
    startOfSection = f.tell()
    sm_i_w(f, 0) #numMaterials
    LOD_mesh_materials = []
    RS_materials = []
    for materialNumber, material in enumerate(mesh.materials):
        RS_material = bf42_material("material_"+str(materialNumber))
        RS_material.texture = material.BF1942_sm_Properties.texture
        RS_material.textureFullPath = material.BF1942_sm_Properties.customTexturePath
        RS_material.transparent = material.BF1942_sm_Properties.transparent
        RS_material.lighting = material.BF1942_sm_Properties.lighting
        RS_material.lightingSpecular = material.BF1942_sm_Properties.lightingSpecular
        RS_material.twosided = material.BF1942_sm_Properties.twosided
        RS_material.envmap = material.BF1942_sm_Properties.envmap
        RS_material.textureFade = material.BF1942_sm_Properties.textureFade
        RS_material.depthWrite = material.BF1942_sm_Properties.depthWrite
        RS_material.blendSrc = material.BF1942_sm_Properties.blendSrc
        RS_material.blendDest = material.BF1942_sm_Properties.blendDest
        RS_material.alphaTestRef = material.BF1942_sm_Properties.alphaTestRef
        RS_material.materialDiffuse = material.BF1942_sm_Properties.materialDiffuse
        RS_material.materialSpecular = material.BF1942_sm_Properties.materialSpecular
        RS_material.materialSpecularPower = material.BF1942_sm_Properties.materialSpecularPower
        RS_materials.append(RS_material)
        faces = []
        vertices = []
        vertexNormals = []
        vertexTextureUV = []
        vertexLightmapUV = []
        vertices_ref = []
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
                    if light_uv_layer == None:
                        vertexLightmapUVco = (0,0)
                    else:
                        vertexLightmapUVco = (light_uv_layer.data[loop_index].uv[0],1-light_uv_layer.data[loop_index].uv[1])
                    ref = (vertex.co, vertexTextureUVco, vertexLightmapUVco)
                    if not ref in vertices_ref:
                        vertices.append((vertex.co[0],vertex.co[2],vertex.co[1]))
                        vertexNormals.append(tuple(vertex.normal))
                        vertexTextureUV.append(vertexTextureUVco)
                        if not light_uv_layer == None and addLightMapUV:
                            vertexLightmapUV.append(vertexLightmapUVco)
                        vertices_ref.append(ref)
                    face.append(vertices_ref.index(ref))
                faces.append((face[0],face[2],face[1])) # correct for normal
        if len(faces) > 0:
            materialSettings = 0
            vertexLightmapUV = vertexLightmapUV if len(vertexLightmapUV)>0 else None
            LOD_mesh_materials.append(sm_LOD_mesh_material("material_"+str(materialNumber), materialSettings, vertices, vertexNormals, vertexTextureUV, vertexLightmapUV, faces))
    for LOD_mesh_material in LOD_mesh_materials:
        LOD_mesh_material.write_1(f)
    for LOD_mesh_material in LOD_mesh_materials:
        LOD_mesh_material.write_2(f)
    
    sizeOfSection = f.tell()-startOfSection-4
    f.seek(startOfSection)
    sm_i_w(f, len(LOD_mesh_materials)) #numMaterials
    f.seek(0,2)
    
    bpy.data.objects.remove(object)
    return(RS_materials)
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
            for material in LOD_mesh.materials:
                print(material.name)
        
        if f.tell() < fileSize: # fix for 'broken' meshes that have EOF after LODs
            hasShadowLods = sm_i(f)
            print("hasShadowLods: "+str(hasShadowLods))
            if hasShadowLods == 1:
                numShadowLods = sm_i(f) # 1 seems to be for number of ShadowLods, is it always 1?
                print("numShadowLods: "+str(numShadowLods))
                for ShadowLodNumber in range(numShadowLods):
                    print('SHADOW_LOD_{}'.format(ShadowLodNumber))
                    LOD_mesh = sm_LOD_mesh().read(f)
    #                for material in LOD_mesh.materials:
    #                    print(material.materialName)
    #                    print(material.numFaces)
            
            PortalMeshBlockSize = sm_i(f)
            print("PortalMeshBlockSize: "+str(PortalMeshBlockSize))
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
                object = bf42_createObject(vertices,faces, fileName+'_COL'+str(collisionMeshNumber+1))
                mesh = object.data
                materialIDs = []
                for i, polygon in enumerate(mesh.polygons):
                    materialID = collisionMesh.faces[i].materialID
                    if not materialID in materialIDs:
                        materialIDs.append(materialID)
                    materialIndex = materialIDs.index(materialID)
                    polygon.material_index = materialIndex
                for materialID in materialIDs:
                    bf42_addMaterialID_Material(mesh,materialID)
                object.scale = (sceneScale,sceneScale,sceneScale)
            endOffset = startOffset+4+collisionMesh.sizeOfSection
            
            if endOffset != f.tell():
                print("\tError!!!!!")
                print('\t{} != {}'.format(f.tell(),endOffset))
                f.seek(endOffset) 
        
        
        numLods = sm_i(f)
        numLodsToPars = numLods
        if add_only_main_LOD: numLodsToPars = min(numLods,1)
        if not add_Visible: numLodsToPars = 0
        for LodNumber in range(numLodsToPars):
            print('LOD_{}'.format(LodNumber))
            bpy.ops.object.select_all(action='DESELECT')
            LOD_mesh = sm_LOD_mesh().read(f)
            print('MATTERIALS_{}'.format(len(LOD_mesh.materials)))
            for materialNumber, material in enumerate(LOD_mesh.materials):
                print('MATTERIAL')
                rs_matterial = rs_materials.get_material(material.name)
                if rs_matterial == False:
                    rs_matterial = bf42_material(material.name)
                # ToDo: add vertexNormals
                object = bf42_createObject(material.vertexValues,material.faces, fileName+'_LOD'+str(LodNumber+1)+'_Material'+str(materialNumber))
                object.scale = (sceneScale,sceneScale,sceneScale)
                mesh = object.data
                texutre_uv_layer = mesh.uv_layers.new(name='textureMap')
                if material.vertexByteSize in [40]:
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
                object.name = fileName+'_LOD'+str(LodNumber+1)
                object.data.name = fileName+'_LOD'+str(LodNumber+1)
                if merge_shared_verticies:
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                    bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
        #skip through rest of lods:
        for LodNumber in range(numLods-numLodsToPars):
            sm_LOD_mesh().read(f)
        
        if f.tell() < fileSize: # fix for 'broken' .sm that have EOF after LODs
            hasShadowLods = sm_i(f)
            if hasShadowLods == 1:
                numShadowLods = sm_i(f) # 1 seems to be for number of ShadowLods, is it always 1?
                for ShadowLodNumber in range(numShadowLods):
                    print('SHADOW_LOD_{}'.format(ShadowLodNumber))
                    LOD_mesh = sm_LOD_mesh().read(f)
                    for materialNumber, material in enumerate(LOD_mesh.materials):
                        object = bf42_createObject(material.vertexValues,material.faces, fileName+'_ShadowLOD')
                        object.scale = (sceneScale,sceneScale,sceneScale)
                    bpy.context.view_layer.objects.active = object
                    if merge_shared_verticies:
                        bpy.ops.object.editmode_toggle()
                        bpy.ops.mesh.remove_doubles(threshold=0.0000, use_unselected=True)
                        bpy.ops.object.editmode_toggle()
                    bpy.ops.object.select_all(action='DESELECT')
        f.close()

def bf42_export_sm(directory, name, BoundingBox_object, COL_objects, LOD_objects, SHADOW_objects, materialID, applyTrans, generateUV, sceneScale):
    print("########### start Export #######")
    directory = bpy.path.abspath(directory)
    if os.path.exists(directory) and name != "":
        path_rs = os.path.join(directory,name+".rs")
        path_sm = os.path.join(directory,name+".sm")
        with open(path_sm, "wb") as f:
            old_active_object = bpy.context.view_layer.objects.active
            
            
            # collision wont work when bb is to small (linux server especially)
            # lod will disapear to soon when bb is to small
            # todo: calculate lod based on all 3: COL1 COL2 LOD1
            if BoundingBox_object != None:
                object = bf42_duplicateSpecialObject(BoundingBox_object)
                if applyTrans:
                    bf42_applyTransformObject(object)
                object.data.transform(Matrix.Scale(1/sceneScale, 4))
                bf42_triangulateObject(object)
                boundingBox = getBoundingBox(object.data)
                bpy.data.objects.remove(object)
            elif len(LOD_objects) > 0: # or should I use col?
                object = bf42_duplicateSpecialObject(LOD_objects[0])
                if applyTrans:
                    bf42_applyTransformObject(object)
                object.data.transform(Matrix.Scale(1/sceneScale, 4))
                bf42_triangulateObject(object)
                boundingBox = getBoundingBox(object.data)
                bpy.data.objects.remove(object)
            elif len(COL_objects) > 0:  # just to be sure 
                object = bf42_duplicateSpecialObject(COL_objects[0])
                if applyTrans:
                    bf42_applyTransformObject(object)
                object.data.transform(Matrix.Scale(1/sceneScale, 4))
                bf42_triangulateObject(object)
                boundingBox = getBoundingBox(object.data) # or should I use col?
                bpy.data.objects.remove(object)
            else:
                boundingBox = [(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]
            
            #header
            sm_i_w(f, 10)
            sm_i_w(f, 0)
            sm_f_w(f, boundingBox)
            sm_B_w(f, 1)
            
            #COLs
            sm_i_w(f, len(COL_objects))
            for COL_object in COL_objects:
                # materialID is None when not forced
                sm_col_export(f, COL_object, materialID, applyTrans, sceneScale)

            
            #LODs
            sm_i_w(f, len(LOD_objects))
            for LOD_Number, LOD_object in enumerate(LOD_objects):
                RS_materials = sm_LOD_export(f, LOD_object, applyTrans, sceneScale, generateUV)
                if LOD_Number == 0:
                    write_rs_file(path_rs,RS_materials)
            
            #Shodow LODs
            hasShadowLods = 1 if len(SHADOW_objects) > 0 else 0
            sm_i_w(f, hasShadowLods)
            if hasShadowLods == 1:
                sm_i_w(f, len(SHADOW_objects))
                for SHADOW_object in SHADOW_objects:
                    sm_LOD_export(f, SHADOW_object, applyTrans, sceneScale)
            
            #Portal Mesh
            PortalMeshBlockSize = 0
            sm_i_w(f, PortalMeshBlockSize)
            
            
            bpy.context.view_layer.objects.active = old_active_object
        remake_sm_BSP(path_sm)
    else:
        print("incorrect directory of filename")
    
    
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