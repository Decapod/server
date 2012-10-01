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

class OutputPathError(Exception): pass
class MultiCaptureError(Exception): pass

class Conventional(object):
    
    trackedMultiCaptureFunc = None
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
        self.cameraPorts = self.cameraController.getPorts()
        
        # retrieve the last capture status
        self.status = Status(FSStore(self.statusFilePath), {"index": 0, "totalCaptures": 0})  
        
        # Creates the directories if they do not exists
        io.makeDirs(self.dataDir)
        io.makeDirs(self.captureDir)
        io.makeDirs(self.exportDir)
    
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
    
    def getImagesByIndex(self, index, filenameTemplate="capture-${cameraID}_${captureIndex}"):
        regex = re.compile(Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex="(?P<index>\d*)"))
        imagePaths = image.imageListFromDir(self.captureDir)
        images = []
        
        for imagePath in imagePaths:
            result = regex.search(imagePath)
            if result.groupdict().get("index") == index:
                images.append(imagePath)
            
        return images;
    
    def deleteImagesByIndex(self, index, filenameTemplate="capture-${cameraID}_${captureIndex}"):
        images = self.getImagesByIndex(index, filenameTemplate)
        for image in images:
            if os.path.exists(image):
                os.remove(image)
                self.status.update("totalCaptures", self.status.model["totalCaptures"] - 1)
    
    def capture(self):
        fileLocations = []
        
        if len(self.cameraPorts) == 0:
            return fileLocations
        
        multiCaptureFunc = Conventional.trackedMultiCaptureFunc if Conventional.trackedMultiCaptureFunc else self.config["multiCapture"]

        # $cameraID is used by the camera capture filename template
        # TODO: Defining the template into config file
        captureNameTemplate = Template("capture-${captureIndex}_${cameraID}").safe_substitute(captureIndex=self.status.model["index"])
        
        multiCapture = getattr(self.cameraController, multiCaptureFunc)
        
        try:
            fileLocations = multiCapture(ports=self.cameraPorts, 
                                         filenameTemplate=captureNameTemplate, 
                                         dir=self.captureDir, 
                                         delay=self.config["delay"],
                                         interval=self.config["interval"])
        except self.cameraController.TimeoutError as e:
            # TODO: fall back to sequential capture
            if len(self.cameraPorts) > 0:
                self.cameraController.releaseCameras()
            
            Conventional.trackedMultiCaptureFunc = "sequentialCapture"
            
            multiCapture = getattr(self.cameraController, Conventional.trackedMultiCaptureFunc)
            
            try:
                fileLocations = multiCapture(ports=self.cameraPorts, 
                                             filenameTemplate=captureNameTemplate, 
                                             dir=self.captureDir)
            except self.cameraController.CaptureError as e:
                raise MultiCaptureError(e.message)
            
        except self.cameraController.CaptureError as e:
            raise MultiCaptureError(e.message)
        
        # Increase the total captures and save
        self.status.update("index", self.status.model["index"] + 1)
        self.status.update("totalCaptures", self.status.model["totalCaptures"] + len(self.cameraPorts))
        
        # TODO: Return a list of URLs to captured images
        return fileLocations
    
    def delete(self):
        io.rmTree(self.dataDir)

    def getStatus(self):
        return self.status.model

