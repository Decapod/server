import os
import sys
from string import Template

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import model
from store import FSStore
from utils import io

class Conventional(object):
    
    initialStatus = {"index": 0, "totalCaptures": 0}
    
    def __init__(self, conventionalDir, captureStatusFile, test=False):
        self.conventionalDir = conventionalDir
        self.captureInfoFilePath = os.path.join(conventionalDir, captureStatusFile)
        
        self.cameraController = cameraInterface if not test else mockCameraInterface
        
        # keep track of the  ports of connected cameras
        self.cameraPorts = self.cameraController.getPorts()
        
        # retrieve the last capture status
        self.fsstore = FSStore(self.captureInfoFilePath)
        self.status = self.fsstore.load()
        
        if (self.status is None):
            self.status = Conventional.initialStatus

        # prepare the change applier for saving status
        self.changeApplier = model.ChangeApplier(self.status)
        self.changeApplier.onModelChanged.addListener("onSaveStatus", self.saveStatus)
        
        # Create the data dir if not exists
        io.makeDirs(conventionalDir)
    
    def saveStatus(self, newModel, oldModel, request):
        self.fsstore.save(newModel)
        
    def capture(self):
        fileLocations = []
        
        # $cameraID is used by the camera capture filename template
        # TODO: Defining the template into config file
        captureNameTemplate = Template("capture-${cameraID}_${captureIndex}.jpg").safe_substitute(captureIndex=self.status["index"])
        
        try:
            fileLocations = self.cameraController.multiCameraCapture(self.cameraPorts, captureNameTemplate, self.conventionalDir)
        except Exception:
            raise
        
        # Increase the total captures and save
        self.changeApplier.requestUpdate("totalCaptures", self.status["totalCaptures"] + len(self.cameraPorts))
        
        return fileLocations
    
    def delete(self):
        io.rmTree(self.conventionalDir)

    def getStatus(self):
        return self.status

