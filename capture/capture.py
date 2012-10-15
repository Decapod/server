import os
import sys
from string import Template
import zipfile
import re

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from status import Status
from store import FSStore
from utils import io, image

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

class OutputPathError(Exception): pass
class CaptureError(Exception): pass
class CameraPortsChangedError(Exception): pass

class Capture(object):
    
    # keep track of the method and camera ports for multiple captures, simultaneous or sequential, 
    # at the class level rather than the instance level. This method is fine with current support  
    # of one single user at a time. It doesn't support the case of having multiple users.
    trackedMultiCaptureFunc = None
    trackedCameraPorts = None
    
    statusAtLastExport = {}
    
    def __init__(self, typeDir, captureStatusFile, config):
        self.typeDir = typeDir
        self.captureDir = os.path.join(self.typeDir, "captures")
        self.exportDir = os.path.join(self.typeDir, "export")
        
        self.config = config
        
        self.statusFilePath = os.path.join(self.typeDir, captureStatusFile)
        self.exportZipFilePath = os.path.join(self.exportDir, "capture.zip")
        
        self.cameraController = cameraInterface if not self.config["testmode"] else mockCameraInterface
        
        # Keep track of the  ports of connected cameras
        Capture.trackedCameraPorts = Capture.trackedCameraPorts if Capture.trackedCameraPorts else self.cameraController.getPorts()
        
        # Creates the directories if they do not exists
        io.makeDirs(self.typeDir)
        io.makeDirs(self.captureDir)
        io.makeDirs(self.exportDir)
    
        # retrieve the last capture status
        self.status = Status(FSStore(self.statusFilePath), {"index": 0, "totalCaptures": 0})  
        
    def getCamerasStatus(self):
        numOfTrackedPorts = len(Capture.trackedCameraPorts)
        
        if numOfTrackedPorts == 0:
            return self.cameraController.generateCameraStatus("NO_CAMERAS")
        
        missingPorts = list(set(self.cameraController.getPorts()) - set(Capture.trackedCameraPorts))
        if missingPorts:
            return self.cameraController.generateCameraStatus("CAMERA_DISCONNECTED", numCamerasDisconnected=len(missingPorts))
        
        try:
            summary = self.cameraController.getAllCamerasSummary()
        except Exception:
            return self.cameraController.generateCameraStatus("NO_CAPTURE")
        
        if numOfTrackedPorts > 2:
            return self.cameraController.generateCameraStatus("TOO_MANY_CAMERAS", cameras=summary)
    
        return self.cameraController.generateCameraStatus("READY")
        
    def export(self):
        isStatusChanged = False;
        for key, val in Capture.statusAtLastExport.iteritems():
            if val is not self.status.model.get(key):
                isStatusChanged = True
                break
        
        # Only create a new zip if one doesn't exist, or if there have been changes.
        if not os.path.exists(self.exportZipFilePath) or isStatusChanged:
            currentDir = os.getcwd()
            os.chdir(self.captureDir)
            io.zip(".", self.exportZipFilePath)
            os.chdir(currentDir)
            Capture.statusAtLastExport = self.status.model.copy()
        
        return self.exportZipFilePath
    
    def getImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex=index)
        return image.findImages(self.captureDir, regexPattern)
    
    def deleteImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex=index)
        removedImages = image.removeImages(self.captureDir, regexPattern)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] - len(removedImages))
        return removedImages
    
    def deleteImages(self):
        removedImages = image.removeImages(self.captureDir)
        
        if removedImages:
            self.status.update("index", 0)
            self.status.update("totalCaptures", 0)
        
    def capture(self):
        fileLocations = []
        
        if len(Capture.trackedCameraPorts) == 0:
            return self.status.model["index"], fileLocations
        
        if self.cameraController.getPorts() != Capture.trackedCameraPorts:
            raise CameraPortsChangedError(self.cameraController.generateCameraStatus("CAMERA_DISCONNECTED"))
        
        multiCaptureFuncName = Capture.trackedMultiCaptureFunc if Capture.trackedMultiCaptureFunc else self.config["multiCapture"]

        # TODO: May want to define the template into config file
        try:
            captureNameTemplate = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(captureIndex=self.status.model["index"])
        except self.cameraController.MultiCaptureError as e:
            raise CaptureError(e.message)
        
        fileLocations, method = self.cameraController.multiCapture(multiCaptureFuncName, Capture.trackedCameraPorts, captureNameTemplate, self.captureDir, self.config["delay"], self.config["interval"])
        
        # Keep track of the determined method for multiple capture
        Capture.trackedMultiCaptureFunc = method
        
        # Increase the total captures and save
        self.status.update("index", self.status.model["index"] + 1)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] + len(Capture.trackedCameraPorts))
        
        # TODO: Return a list of URLs to captured images
        return self.status.model["index"], fileLocations
    
    def delete(self):
        io.rmTree(self.typeDir)
        self.status.update("index", 0)
        self.status.update("totalCaptures", 0)

    def getStatus(self):
        return self.status.model

