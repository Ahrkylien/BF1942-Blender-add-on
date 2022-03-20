import os
import bpy
import struct
from math import sqrt, pow

def bf42_readTGAHeader(f):
    f.seek(0,2)
    NRofBytes = f.tell()
    f.seek(0)
    if NRofBytes<=18:
        print("Error: TGA wrong size")
        return(False)
    f.read(12) #some header stuff
    width = struct.unpack('H', f.read(2))[0]
    height = struct.unpack('H', f.read(2))[0]
    if width<=0 or height<=0:
        return(False)
    bitDepth = struct.unpack('B', f.read(1))[0]
    if bitDepth not in [24,32]:
        print("Error: bitDepth is not 24 or 32")
        return(False)
    f.read(1) #some header stuff
    # //Check if file size corresponds to the image dimensions:
    if width*height*3+18 > NRofBytes:
        print("Error: TGA wrong size")
        return(False)
    return(bitDepth, width, height)
    
def bf42_writeTGAHeader(f, width, height, bitDepth=24):
    f.write(struct.pack('B'*12, *[0,0,2,0,0,0,0,0,0,0,0,0]))
    #width,height:
    f.write(struct.pack('H', width))
    f.write(struct.pack('H', height))
    #bitDepth
    f.write(struct.pack('B', bitDepth))
    #header stuff:
    f.write(struct.pack('B', 0))
    
    
def bf42_TGA_substract(pathCombined, pathDiffuse, pathGenerated):
    for file in os.listdir(pathCombined):
        if file.lower().endswith(".tga"):
            fileName = os.path.basename(file).split(".",1)[0]
            print("##### Substracting: "+fileName)
            fileCombined = os.path.join(pathCombined,fileName+".tga")
            fileDiffuse = os.path.join(pathDiffuse,fileName+".tga")
            fileGenerated = os.path.join(pathGenerated,fileName+".tga")
            try:
                f = open(fileCombined, 'rb')
                f2 = open(fileDiffuse, 'rb')
            except IOError:
                print("Error: One of the input files is not accessible")
                return(False)
            else:
                TGA = bf42_readTGAHeader(f)
                TGA2 = bf42_readTGAHeader(f2)
                if TGA == False:
                    return(False)
                else:
                    (bitDepth, width, height) = TGA
                    (bitDepth2, width2, height2) = TGA2
                    try:
                        fnew = open(fileGenerated, 'wb')
                    except IOError:
                        print("Error: output file is not accessible")
                        return(False)
                    else:
                        N = width*height
                        f.seek(18)
                        f2.seek(18)
                        bf42_writeTGAHeader(fnew, width, height, bitDepth2)
                        for x in range(N):
                            for i in range(3):
                                col1 = struct.unpack('B', f.read(1))[0]
                                col2 = struct.unpack('B', f2.read(1))[0]
                                newCol = 0 if col2 == 0 else (col1/(2*col2))*255
                                newCol = int(min(255,max(0,newCol)))
                                newCol = int(min(2*col2,newCol))
                                fnew.write(struct.pack('B', newCol))
                            if bitDepth2 == 32:
                                fnew.write(f2.read(1)) # alpha from Diffuse
                            if bitDepth == 32:
                                f.read(1)
                        fnew.close()
                    f.close()
                    f2.close()
    
def bf42_TGA_average(average, pathSource, pathGenerated):
    Desired_average = average.copy()
    Desired_average.reverse() #to BGR
    for i in range(3):
        col = Desired_average[i]
        if col < 0.0031308:
            Desired_average[i] = 0.0 if col < 0.0 else col * 12.92
        else:
            Desired_average[i] = 1.055 * pow(col, 1.0 / 2.4) - 0.055
        Desired_average[i] = max(0, min(1, Desired_average[i]))
    
    for file in os.listdir(pathSource):
        if file.lower().endswith(".tga"):
            fileName = os.path.basename(file).split(".",1)[0]
            print("##### Substracting: "+fileName)
            fileSource = os.path.join(pathSource,fileName+".tga")
            fileGenerated = os.path.join(pathGenerated,fileName+".tga")
            try:
                f = open(fileSource, 'rb')
            except IOError:
                print("Error: One of the input files is not accessible")
                return(False)
            else:
                TGA = bf42_readTGAHeader(f)
                if TGA == False:
                    return(False)
                else:
                    (bitDepth, width, height) = TGA
                    try:
                        fnew = open(fileGenerated, 'wb')
                    except IOError:
                        print("Error: output file is not accessible")
                        return(False)
                    else:
                        N = width*height
                        # Desired_SUM = [x*N*255 for x in Desired_average]
                        Alpha_weight = 0
                        SUM = [0,0,0]
                        f.seek(18)
                        for x in range(N):
                            blue = struct.unpack('B', f.read(1))[0]
                            green = struct.unpack('B', f.read(1))[0]
                            red = struct.unpack('B', f.read(1))[0]
                            alpha = struct.unpack('B', f.read(1))[0]
                            SUM[0] += blue*alpha
                            SUM[1] += green*alpha
                            SUM[2] += red*alpha
                            Alpha_weight += alpha
                        Desired_SUM = [Desired_average[i]*255*Alpha_weight for i in range(3)]
                        shift = [round((Desired_SUM[i]-SUM[i])/Alpha_weight) for i in range(3)]
                        
                        print(SUM)
                        print(Alpha_weight)
                        print(Desired_SUM)
                        print(shift)
                        bf42_writeTGAHeader(fnew, width, height, bitDepth)
                        f.seek(18)
                        for x in range(N):
                            for i in range(3):
                                col = struct.unpack('B', f.read(1))[0]
                                newCol = int(min(255,max(0,col+shift[i])))
                                fnew.write(struct.pack('B', newCol))
                            if bitDepth == 32:
                                fnew.write(f.read(1))
                        f.close()

def bf42_TGA_denoise(pathSource, pathGenerated):
    bpy.context.scene.use_nodes = True
    nodeTree = bpy.context.scene.node_tree
    nodes = nodeTree.nodes
    for node in nodes:
        nodes.remove(node)
    
    bpy.context.scene.render.image_settings.file_format = 'TARGA_RAW'
    
    images = []
    for file in os.listdir(pathSource):
        if file.lower().endswith(".tga"):
            fileName = file.split(".",1)[0]
            
            node_image = nodes.new(type="CompositorNodeImage")
            node_denoise = nodes.new(type="CompositorNodeDenoise")
            node_output = nodes.new(type="CompositorNodeOutputFile")

            links = nodeTree.links
            new_link = links.new(node_image.outputs[0],node_denoise.inputs[0])
            new_link = links.new(node_denoise.outputs[0],node_output.inputs[0])

            image = bpy.data.images.load(os.path.join(pathSource,file))
            node_image.image = image
            images.append(image)

            node_output.base_path = os.path.join(pathGenerated,"TMP_Conv_"+fileName)

    
    bpy.ops.render.render()

    # for image in images:
        # bpy.data.images.remove(image)

    for subdir, dirs, files in os.walk(pathGenerated):
        subdirName = os.path.basename(subdir)
        if subdirName.startswith("TMP_Conv_") and len(files) == 1:
            os.replace(os.path.join(subdir, files[0]), os.path.join(pathGenerated, subdirName[len("TMP_Conv_"):]+".tga"))
            os.rmdir(subdir)

def bf42_raw_to_TGA(fileSource, fileGenerated):
    fileName = os.path.basename(fileSource).split(".",1)[0]
    print("##### Converting: "+fileName)
    try:
        fin = open(fileSource, 'rb')
        fout = open(fileGenerated, 'wb')
    except IOError:
        print("Error: Input file is not accessible")
        return(False)
    else:
        fin.seek(0,2)
        NRofBytes = fin.tell()
        fin.seek(0)
        width = int(sqrt(NRofBytes))

        bf42_writeTGAHeader(fout, width, width)

        for i in range(width**2):
            fread = fin.read(1)
            for j in range(3):
                fout.write(fread)

        fout.close()
        fin.close()