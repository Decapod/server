import os

from utils import io

class FSStore(object):
    def __init__(self, filePath):
        self.filePath = filePath

    def load(self):
        if not os.path.exists(self.filePath): 
            return None
        else:
            return io.loadJSONFile(self.filePath)
            
    def save(self, aDict):
        io.writeToJSONFile(aDict, self.filePath)
