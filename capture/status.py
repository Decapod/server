import os
import sys
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from utils import io

class Status(object):
    
    def __init__(self, conventionalDir, captureStatusFile, test=False):
        self.captureInfoFilePath = os.path.join(conventionalDir, captureStatusFile)
        
        # Create the data dir if not exists
        io.makeDirs(conventionalDir)
    
    def getStatus(self):
        returnInfo = {}
        
        content = io.readFromFile(self.captureInfoFilePath)
        
        if content is None: returnInfo = json.dumps(returnInfo)
        else: returnInfo = content
        
        return returnInfo
