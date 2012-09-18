import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource
from utils import io

CONVENTIONAL_DATA_DIR = os.path.join("${data}", "conventional")

captureInfoFileName = "captureStatus.json"

class Conventional(object):
    
    def __init__(self, test=False):
        self.rs = resourcesource
        self.dataDir = self.rs.path(CONVENTIONAL_DATA_DIR)
        self.captureInfoFilePath = os.path.join(self.dataDir, captureInfoFileName)
        
        # Create the data dir if not exists
        io.makeDirs(self.dataDir)
    
    def getStatus(self):
        content = io.readFromFile(self.captureInfoFilePath)
        
        if content is None: returnInfo = {}
        else: returnInfo = content
        
        return returnInfo
