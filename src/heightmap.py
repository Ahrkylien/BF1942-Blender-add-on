import os
import bpy
from math import sqrt

from .misc import *

class bf42_heightmap:
    def __init__(self, yScale=1, SceneScale=0.01):
        self.SceneScale = SceneScale
        self.SceneScaleInv = 1/SceneScale
        self.yScale = yScale
        self.worldSize = 0
        self.worldDim = 0
        self.importMapPath = ""
        self.exportMapPath = ""
        self.resetErrors()
    
    def resetErrors(self):
        self.fileERROR = False
        self.fileERRORMessage = ""
    
    def addImportMapPath(self, path):
        self.resetErrors()
        self.importMapPath = path
        self.checkFile()
    
    def addExportMapPath(self, path):
        self.exportMapPath = os.path.join(path,"Heightmap.raw")
    
    def setWorldSize(self, worldSize):
        self.worldSize = int(worldSize)
        self.worldDim = int(worldSize/4)
    
    def checkFile(self):
        NRofBytes = int(os.path.getsize(self.importMapPath))
        
        self.worldSize = int(sqrt(NRofBytes*8))
        self.worldDim = int(self.worldSize/4)
        
        if NRofBytes != self.worldDim*self.worldDim*2:
            self.fileERRORMessage += "File size is incorrect.\n"
            self.fileERROR = True
    
    def generateMesh(self):
        self.resetErrors()
        if self.importMapPath != "":
            vertices = []
            edges = []
            faces = []
            
            try:
                f = open(self.importMapPath, 'rb')
            except IOError:
                print("File not accessible")
            else:
                fileContent = f.read()
                for x in range(self.worldDim):
                    for y in range(self.worldDim):
                        baseIndex = int(2*(x + (y*self.worldDim)))
                        unsigned16bit = fileContent[baseIndex+1]*256 + fileContent[baseIndex]
                        height = 256*self.yScale*(unsigned16bit/65535)
                        vertices.append((x*4,y*4,height))
                f.close()
                
                for x in range(self.worldDim-1):
                    for y in range(self.worldDim-1):
                        index = y*self.worldDim+x
                        if (y+x) % 2 == 0:
                            faces.append((index+1,index,index+self.worldDim+1))
                            faces.append((index+self.worldDim+1,index,index+self.worldDim))
                        else:
                            faces.append((index+1,index,index+self.worldDim))
                            faces.append((index+self.worldDim+1,index+1,index+self.worldDim))

            
            terrain_mesh = bpy.data.meshes.new('terrain')
            terrain_mesh.from_pydata(vertices, edges, faces)
            terrain_mesh.update()
            terrain_object = bpy.data.objects.new('terrain', terrain_mesh)
            terrain_uv_layer = terrain_mesh.uv_layers.new(name='uvMap')
            for loop in terrain_object.data.loops:
                vertex = terrain_object.data.vertices[loop.vertex_index]
                terrain_uv_layer.data[loop.index].uv = (2*vertex.co[0]/self.worldSize-.5,2*vertex.co[1]/self.worldSize-.5)
            bf42_addSpecialObject(terrain_object)
            terrain_object.scale = (self.SceneScale, self.SceneScale, self.SceneScale)
    
    def generateWaterMesh(self, waterLevel):
        vertices = [(0,0,waterLevel),(0,self.worldSize,waterLevel),(self.worldSize,self.worldSize,waterLevel),(self.worldSize,0,waterLevel),]
        edges = []
        faces = [(0,1,2,3)]
        
        water_mesh = bpy.data.meshes.new('water')
        water_mesh.from_pydata(vertices, edges, faces)
        water_mesh.update()
        water_object = bpy.data.objects.new('water', water_mesh)
        water_uv_layer = water_mesh.uv_layers.new(name='uvMap')
        for loop in water_object.data.loops:
            vertex = water_object.data.vertices[loop.vertex_index]
            water_uv_layer.data[loop.index].uv = (vertex.co[0]/self.worldSize,vertex.co[1]/self.worldSize)
        
        bf42_addSpecialObject(water_object)
        water_object.scale = (self.SceneScale, self.SceneScale, self.SceneScale)
    
    def generateHeightmap(self, object):
        terrain_object = bf42_duplicateSpecialObject(object)
        terrain_object.data.transform(terrain_object.matrix_world)
        terrain_object.matrix_world = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))
        
        binaryList = []
        for y in range(0,self.worldSize,4):
            for x in range(0,self.worldSize,4):
                result, location, normal, index = terrain_object.ray_cast([x/self.SceneScaleInv,y/self.SceneScaleInv,1000],[0,0,-1])
                height=0
                if result:
                    height = min(max(location[2]*self.SceneScaleInv,0),256*self.yScale)
                int16 = round(65535*height/(256*self.yScale))
                int8_2 = int16 >> 8
                int8_1 = int16 & 255
                binaryList.append(int8_1)
                binaryList.append(int8_2)
        bpy.data.objects.remove(terrain_object)
        
        f=open(self.exportMapPath,"wb")
        f.write(bytearray(binaryList))
        f.close()