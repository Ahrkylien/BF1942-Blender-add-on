import bpy

from .bf42_script import bf42_vec3
from .misc import *

def bf42_importAreaObject(objectTemplate, sceneScale = 1):
    vertices = []
    for linePoint in objectTemplate.linePoints:
        vertices.append((linePoint.x*sceneScale,linePoint.y*sceneScale,0))
    edges = []
    for i in range(len(vertices)-1):
        edges.append((i,i+1)) 
    object = bf42_createAreaObject(vertices, edges, objectTemplate.name)
    return(object)