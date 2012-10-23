import os
import sys
from string import Template
from zipfile import ZipFile
import re

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
from status import Status
from store import FSStore
from utils import io, image

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${index}_${cameraID}"

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
        numOfTrackedPorts = len(self.cameraController.getPorts())
        
        if numOfTrackedPorts == 0:
            return self.cameraController.generateCameraStatus("NO_CAMERAS")
        
        missingPorts = list(set(Capture.trackedCameraPorts) - set(self.cameraController.getPorts()))
        if missingPorts:
            return self.cameraController.generateCameraStatus("CAMERA_DISCONNECTED", numCamerasDisconnected=len(missingPorts))
        elif Capture.trackedCameraPorts != self.cameraController.getPorts():
            # More cameras are connected, retrack
            Capture.trackedCameraPorts = self.cameraController.getPorts()
            
        try:
            summary = self.cameraController.getAllCamerasSummary()
        except Exception:
            return self.cameraController.generateCameraStatus("NO_CAPTURE")
        
        if numOfTrackedPorts > 2:
            return self.cameraController.generateCameraStatus("TOO_MANY_CAMERAS", cameras=summary)
    
        return self.cameraController.generateCameraStatus("READY")
    
    def indices(self, fileName):
        pattern = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(index="(?P<index>\d+?)", cameraID="(?P<cameraID>\d+?)")
        regex = re.compile(pattern)
        r = regex.search(fileName)
        group = r.groupdict()   
        return int(group.get("index", 0)), int(group.get("cameraID", 0))
    
    def sort(self, reverse=False):
        regexPattern = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(cameraID="\d*", index="\d*")
        return sorted(image.findImages(self.captureDir, regexPattern), key=self.indices, reverse=reverse)
    
    def export(self):
        isStatusChanged = False;
        for key, val in Capture.statusAtLastExport.iteritems():
            if val is not self.status.model.get(key):
                isStatusChanged = True
                break
        
        # Only create a new zip if one doesn't exist, or if there have been changes.
        if not os.path.exists(self.exportZipFilePath) or isStatusChanged:
            position = 0;
            currentIndex = 0;
            currentDir = os.getcwd()
            os.chdir(self.captureDir)
            
            zFile = ZipFile(self.exportZipFilePath, mode="w")
        
            for imagePath in self.sort():
                fileName = os.path.basename(imagePath)
                index, cameraID = self.indices(fileName)
                
                if currentIndex is not index:
                    currentIndex = index
                    position = position + 1
                    
                arcName = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(index=position, cameraID=cameraID) + os.path.splitext(fileName)[1]
                zFile.write(fileName, arcName)

            
            zFile.close()
            
            os.chdir(currentDir)
            Capture.statusAtLastExport = self.status.model.copy()
        
        return self.exportZipFilePath
    
    def getImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", index=index)
        return image.findImages(self.captureDir, regexPattern)
    
    def deleteImagesByIndex(self, index, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", index=index)
        removedImages = image.removeImages(self.captureDir, regexPattern)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] - 1)
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
            nextIndex = self.status.model["index"] + 1
            captureNameTemplate = Template(DEFAULT_CAPTURE_NAME_TEMPLATE).safe_substitute(index=nextIndex)
        except self.cameraController.MultiCaptureError as e:
            raise CaptureError(e.message)
        
        fileLocations, method = self.cameraController.multiCapture(multiCaptureFuncName, Capture.trackedCameraPorts, captureNameTemplate, self.captureDir, self.config["delay"], self.config["interval"])
        
        # Keep track of the determined method for multiple capture
        Capture.trackedMultiCaptureFunc = method
        
        # Increase the total captures and save
        self.status.update("index", nextIndex)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] + 1)
        
        # TODO: Return a list of URLs to captured images
        return self.status.model, fileLocations
    
    def delete(self):
        io.rmTree(self.typeDir)
        self.status.update("index", 0)
        self.status.update("totalCaptures", 0)
        Capture.trackedCameraPorts = self.cameraController.getPorts()

    def getStatus(self):
        return self.status.model

