

class Map:
    def __init__(self, data=None):
        if data==None: data={}
        self.data=data
    def has(self, name):
        return name in self.data
    def get(self, name, defVal=None):
        if not name in self.data:
            return defVal
        return self.data[name]
    def put(self, name, value):
        self.data[name]=value
    def getInt(self, name, defVal=None):
        if not name in self.data:
            return defVal
        try:
            return int(self.data[name])
        except:
            return defVal
    def getString(self, name, defVal=None):
        if not name in self.data or self.data[name]==None:
            return defVal
        try:
            return str(self.data[name])
        except:
            return defVal
    def getBool(self, name, defVal=False):
        if not name in self.data:
            return defVal
        try:
            return bool(self.data[name])
        except:
            return defVal
    def getFloat(self, name, defVal=None):
        if not name in self.data:
            return defVal
        try:
            return float(self.data[name])
        except:
            return defVal
        