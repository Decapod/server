import os
import sys
from string import Template
import zipfile
import re

import cameraInterface
import mockCameraInterface
import captureErrors
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from status import Status
from store import FSStore
from utils import io, image

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

class OutputPathError(Exception): pass
class CaptureError(Exception): pass
class CameraPortsChangedError(Exception): pass

class Conventional(object):
    
    # keep track of the method and camera ports for multiple captures, simultaneous or sequential, 
    # at the class level rather than the instance level. This method is fine with current support  
    # of one single user at a time. It doesn't support the case of having multiple users.
    trackedMultiCaptureFunc = None
    trackedCameraPorts = None
    
    statusAtLastExport = {}
    
    def __init__(self, dataDir, captureStatusFile, config):
        self.dataDir = dataDir
        self.captureDir = os.path.join(self.dataDir, "captures")
        self.exportDir = os.path.join(self.dataDir, "export")
        
        self.config = config
        
        self.statusFilePath = os.path.join(self.dataDir, captureStatusFile)
        self.exportZipFilePath = os.path.join(self.exportDir, "conventional.zip")
        
        self.cameraController = cameraInterface if not self.config["testmode"] else mockCameraInterface
        
        # Keep track of the  ports of connected cameras
        Conventional.trackedCameraPorts = Conventional.trackedCameraPorts if Conventional.trackedCameraPorts else self.cameraController.getPorts()
        
        # retrieve the last capture status
        self.status = Status(FSStore(self.statusFilePath), {"index": 0, "totalCaptures": 0})  
        
        # Creates the directories if they do not exists
        io.makeDirs(self.dataDir)
        io.makeDirs(self.captureDir)
        io.makeDirs(self.exportDir)
    
    def getCamerasStatus(self):
        if len(Conventional.trackedCameraPorts) == 0:
            return captureErrors.generateErrorInfo("NO_CAMERAS")
        
        if len(Conventional.trackedCameraPorts) > 2:
            return captureErrors.generateErrorInfo("TOO_MANY_CAMERAS")
        
        if self.cameraController.getPorts() != Conventional.trackedCameraPorts:
            return captureErrors.generateErrorInfo("CAMERA_DISCONECTED")
        
    def export(self):
        isStatusChanged = False;
        for key, val in Conventional.statusAtLastExport.iteritems():
            if val is not self.status.model.get(key):
                isStatusChanged = True
                break
        
        # Only create a new zip if one doesn't exist, or if there have been changes.
        if not os.path.exists(self.exportZipFilePath) or isStatusChanged:
            currentDir = os.getcwd()
            os.chdir(self.captureDir)
            io.zip(".", self.exportZipFilePath)
            os.chdir(currentDir)
            Conventional.statusAtLastExport = self.status.model.copy()
        
        return self.exportZipFilePath
    
    def getImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex=index)
        return image.findImages(self.captureDir, regexPattern)
    
    def deleteImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex=index)
        removedImages = image.removeImages(self.captureDir, regexPattern)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] - len(removedImages))
        return removedImages
    
    def capture(self):
        fileLocations = []
        
        if len(Conventional.trackedCameraPorts) == 0:
            return fileLocations
        
        if self.cameraController.getPorts() != Conventional.trackedCameraPorts:
            raise CameraPortsChangedError("Camera ports has been changed.")
        
        multiCaptureFuncName = Conventional.trackedMultiCaptureFunc if Conventional.trackedMultiCaptureFunc else self.config["multiCapture"]

        # $cameraID is used by the camera capture filename template
        # TODO: May want to define the template into config file
        try:
            captureNameTemplate = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(captureIndex=self.status.model["index"])
        except self.cameraController.MultiCaptureError as e:
            raise CaptureError(e.message)
        
        fileLocations, method = self.cameraController.multiCapture(multiCaptureFuncName, Conventional.trackedCameraPorts, captureNameTemplate, self.captureDir, self.config["delay"], self.config["interval"])
        
        # Keep track of the determined method for multiple capture
        Conventional.trackedMultiCaptureFunc = method
        
        # Increase the total captures and save
        self.status.update("index", self.status.model["index"] + 1)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] + len(Conventional.trackedCameraPorts))
        
        # TODO: Return a list of URLs to captured images
        return fileLocations
    
    def delete(self):
        io.rmTree(self.dataDir)

    def getStatus(self):
        return self.status.model

