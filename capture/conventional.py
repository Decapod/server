import os
import sys
import zipfile

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import model
from store import FSStore
from utils import io

class OutputPathError(Exception): pass

class Conventional(object):
    
    initialStatus = {"index": 0, "totalCaptures": 0}
    
    def __init__(self, dataDir, captureStatusFile, test=False):
        self.dataDir = dataDir
        self.captureInfoFilePath = os.path.join(dataDir, captureStatusFile)
        self.exportZipFilePath = os.path.join(self.dataDir, "..", "conventional.zip")
        
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
        io.makeDirs(dataDir)
    
    def saveStatus(self, newModel, oldModel, request):
        self.fsstore.save(newModel)
        
    def export(self):
        try:
            zip = zipfile.ZipFile(self.exportZipFilePath, mode="w")
        except IOError:
            raise OutputPathError("{0} is not a valid path".format(self.exportZipFilePath))
        
        os.chdir(self.dataDir)
        
        for file in os.listdir("."):
            zip.write(file)
        zip.close()
        
        return self.exportZipFilePath
        
    def capture(self):
        fileLocations = []
        
        # Use the string keyword format to keep {0} intact which is used by the camera capture filename template
        # TODO: Defining the template into config file
        captureNameTemplate = "capture-{0}_{1}.jpg".format(self.status["index"], "{0}")
        
        try:
            fileLocations = self.cameraController.multiCameraCapture(self.cameraPorts, captureNameTemplate, self.dataDir)
        except Exception:
            raise
        
        # Increase the total captures and save
        self.changeApplier.requestUpdate("index", self.status["index"] + 1)
        self.changeApplier.requestUpdate("totalCaptures", self.status["totalCaptures"] + len(self.cameraPorts))
        
        # TODO: Return a list of URLs to captured images
        return fileLocations
    
    def delete(self):
        io.rmTree(self.dataDir)

    def getStatus(self):
        return self.status

