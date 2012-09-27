import os
import sys
from string import Template
import zipfile
import re

import cameraInterface
import mockCameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import model
from store import FSStore
from utils import io, image

class OutputPathError(Exception): pass
class MultiCaptureError(Exception): pass

class Conventional(object):
    
    initialStatus = {"index": 0, "totalCaptures": 0}
    trackedMultiCaptureFunc = None
    
    def __init__(self, dataDir, captureStatusFile, config):
        self.dataDir = dataDir
        self.config = config
        
        self.captureInfoFilePath = os.path.join(dataDir, captureStatusFile)
        self.exportZipFilePath = os.path.join(self.dataDir, "..", "conventional.zip")
        
        self.cameraController = cameraInterface if not self.config["testmode"] else mockCameraInterface
        
        # Keep track of the  ports of connected cameras
        self.cameraPorts = self.cameraController.getPorts()
        
        # retrieve the last capture status
        self.fsstore = FSStore(self.captureInfoFilePath)
        self.status = self.fsstore.load()
        
        if (self.status is None):
            self.status = Conventional.initialStatus

        # Prepare the change applier for saving status
        self.changeApplier = model.ChangeApplier(self.status)
        self.changeApplier.onModelChanged.addListener("onSaveStatus", self.saveStatus)
        
        # Create the data dir if not exists
        io.makeDirs(dataDir)
    
    def saveStatus(self, newModel, oldModel, request):
        self.fsstore.save(newModel)
        
    def export(self):
        currentDir = os.getcwd()
        try:
            zip = zipfile.ZipFile(self.exportZipFilePath, mode="w")
        except IOError:
            raise OutputPathError("{0} is not a valid path".format(self.exportZipFilePath))
        
        os.chdir(self.dataDir)
        
        for file in os.listdir("."):
            zip.write(file)
        zip.close()
        os.chdir(currentDir)
        
        return self.exportZipFilePath
    
    def getImagesByIndex(self, index, filenameTemplate="capture-${cameraID}_${captureIndex}"):
        regex = re.compile(Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex="(?P<index>\d*)"))
        imagePaths = image.imageListFromDir(self.dataDir)
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
                self.changeApplier.requestUpdate("totalCaptures", self.status["totalCaptures"] - 1)
    
    def capture(self):
        fileLocations = []
        
        if len(self.cameraPorts) == 0:
            return fileLocations
        
        multiCaptureFunc = Conventional.trackedMultiCaptureFunc if Conventional.trackedMultiCaptureFunc else self.config["multiCapture"]

        # $cameraID is used by the camera capture filename template
        # TODO: Defining the template into config file
        captureNameTemplate = Template("capture-${captureIndex}_${cameraID}.jpg").safe_substitute(captureIndex=self.status["index"])
        
        multiCapture = getattr(self.cameraController, multiCaptureFunc)
        
        try:
            fileLocations = multiCapture(ports=self.cameraPorts, 
                                         filenameTemplate=captureNameTemplate, 
                                         dir=self.dataDir, 
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
                                             dir=self.dataDir)
            except self.cameraController.CaptureError as e:
                raise MultiCaptureError(e.message)
            
        except self.cameraController.CaptureError as e:
            raise MultiCaptureError(e.message)
        
        # Increase the total captures and save
        self.changeApplier.requestUpdate("index", self.status["index"] + 1)
        self.changeApplier.requestUpdate("totalCaptures", self.status["totalCaptures"] + len(self.cameraPorts))
        
        # TODO: Return a list of URLs to captured images
        return fileLocations
    
    def delete(self):
        io.rmTree(self.dataDir)

    def getStatus(self):
        return self.status

