# vec3
class bf42_vec3:
    x = 0
    y = 0
    z = 0
    def __init__(self, vertex):
        if type(vertex) is str:
            v = [float(vert) for vert in vertex.split('/')]
            if len(v) != 3:
                print(vertex)
                return(0)
            self.x = v[0]
            self.y = v[2]
            self.z = v[1]
        else:
            self.x = vertex[0]
            self.y = vertex[1]
            self.z = vertex[2]
    def str(self, dec):
        return ("%.*f %.*f %.*f" % (dec, self.x, dec, self.y, dec, self.z))
# object class
class bf42_Object:
    name = None
    absolutePosition = bf42_vec3('0/0/0')
    rotation = bf42_vec3('0/0/0')
    index = 0
    template = None
    def __init__(self, name):
        self.name = name
# parses .con file and returns list of objects
def bf42_ParseCon(filename):
    objects = []
    with open(filename, 'r') as fp:
        for line in fp.readlines():
            
            # split line by spaces
            words = line.lower().strip().split(' ')
            
            # object.create
            if words[0] == 'object.create':
                objects.append( bf42_Object( words[1] ) )
            
            # .absoluteposition
            if words[0] == 'object.absoluteposition':
                objects[-1].absolutePosition = bf42_vec3( words[1] )
            
            # .rotation
            if words[0] == 'object.rotation':
                objects[-1].rotation = bf42_vec3( words[1] )
    return objects