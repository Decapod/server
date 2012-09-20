import os
import sys

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from utils import io

class Conventional(object):
    
    def __init__(self, conventionalDir, captureStatusFile, test=False):
        self.conventionalDir = conventionalDir
        self.captureInfoFilePath = os.path.join(conventionalDir, captureStatusFile)
        
        self.cameraController = cameraInterface if not test else mockCameraInterface
        
        # keep track of the  ports of connected cameras
        self.cameraPorts = self.cameraController.getPorts()
        
        # ToDo: retrieve the last capture status
        self.status = {"index": 0, "totalCaptures": 0}

        # Create the data dir if not exists
        io.makeDirs(conventionalDir)
    
    def capture(self):
        fileLocations = []
        captureNameTemplate = "capture-" + str(self.status["index"]) + "_{0}.jpg"
        
        try:
            fileLocations = self.cameraController.multiCameraCapture(self.cameraPorts, captureNameTemplate, self.conventionalDir)
        except Exception:
            raise
        
        # ToDo: increase the total captures and save
        self.status["totalCaptures"] = self.status["totalCaptures"] + len(self.cameraPorts)
        
        return fileLocations
    
    def delete(self):
        io.rmTree(self.conventionalDir)

    def getStatus(self):
        return self.status

