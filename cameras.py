import os
import glob
import subprocess
from PIL import Image
import simplejson as json
import decapod_utilities as utils

CAPTURE_DIR = "${book}/capturedImages/"
CALIBRATION_DIR = "${calibrationImages}/"
imagePrefix = "decapod-"

class CameraError(Exception): pass
class CaptureError(CameraError): pass

class Cameras(object):
    
    imageIndex = 0;
    cameraSupportConfig = None
    supportedModels = None
    resources = None
    _calibration = None
    serialNumberPortMap = {}
    
    def __init__(self, resourceSource, cameraConfig):
        self.resources = resourceSource
        
        # Load the supported cameras configuration.
        supportedCamerasPath = self.resources.filePath(cameraConfig)
        supportedCamerasJSON = open(supportedCamerasPath)
        self.cameraSupportConfig = json.load(supportedCamerasJSON)
        self.supportedModels = self.mapSupportedCamerasToModelList()
                
        # Setup the capture locations.
        utils.mkdirIfNecessary(self.resources.filePath(CAPTURE_DIR))
        utils.remakeDir(self.resources.filePath(CALIBRATION_DIR))

    def calibrationModel(self, updatedModel=None):
        # TODO: This code sucks.
        # Get
        if updatedModel is None:
            if self._calibration is None:
                self._calibration = self.defaultCalibrationModel()
            return self._calibration
        
        # Set
        self._calibration = updatedModel
    
    def serialNumberForPort(self, port):
        serialNumberToken = "Serial Number: "
        serialNumberTokenLen = 15
        
        summaryCmd = [
            "gphoto2",
            "--summary",
            "--port=%s" % port
        ]
        summary = utils.invokeCommandSync(summaryCmd, 
                                         CameraError,
                                         "An error occurred while attempting to summarize the camera connected on port %s." \
                                         % port)
        summaryLines = summary.split("\n") # TODO: Check cross-platform compatibility here.
        
        # Return the first match found after the string "Serial Number: "
        for line in summaryLines:
            serialNumIdx = line.find(serialNumberToken)
            if serialNumIdx > -1:
                serialNumIdx = serialNumIdx + serialNumberTokenLen
                serialNum = line[serialNumIdx:]
                return serialNum
        
        return None
    
    def serialNumbers(self):
        ports = self.cameraPortsAscending()
        serials = []
        for port in ports:
            serial = self.serialNumberForPort(port)
            self.serialNumberPortMap[serial] = port
            serials.append(serial)
        return serials

    
    def cameraPortsAscending(self):
        cameraInfo = self.cameraInfo()
        
        if len(cameraInfo) < 2:
            raise CameraError, "Two cameras are not currently connected."
        
        ports = [
            cameraInfo[0]["port"], 
            cameraInfo[1]["port"]
        ]
        ports.sort()
        return ports
        
    def defaultCalibrationModel(self):
        cameraIDs = self.serialNumbers()
        calibration = {
            "left": {
                "id": cameraIDs[0],
                "rotation": 0
            },
            "right": {
                "id": cameraIDs[1],
                "rotation": 0
            }                
        }
        return calibration
    
    def cameraInfo(self):
        """Detects the cameras locally attached to the PC.
           Returns a JSON document, describing the camera and its port."""
 
        detectCmd = [
            "gphoto2",
            "--auto-detect"
        ]
        cmdOutput = utils.invokeCommandSync(detectCmd, 
                                            CameraError,
                                            "An error occurred while attempting to detect cameras.")
        allCamerasInfo = cmdOutput.split("\n")[2:] # TODO: Check cross-platform compatibility here.

        # TODO: Is there a saner algorithm here?
        cameras = []
        for cameraInfo in allCamerasInfo:
            # Skip any camera that has a port ending in ":", since these aren't real devices.
            if cameraInfo.strip().endswith(":") is True:
                continue
            
            # TODO: Can we improve this algorithm?
            # Tokenize the line on spaces, grab the last token, and assume it's the port
            # Then stitch the rest of the tokens back and assume that they're the model name.
            tokens = cameraInfo.split()
            if len(tokens) < 1:
                continue
            port = tokens.pop()
            camera = {
                "port": port,
                "model": " ".join(tokens),
                "capture": True, # TODO: Remove this property
                "download": True # TODO: Remove this property
            }
            cameras.append(camera)
        
        return cameras
    
    def mapSupportedCamerasToModelList(self):
        supportedCameras = self.cameraSupportConfig["supportedCameras"]
        supportedModels = []
        
        for brand in supportedCameras.values():
            modelsForBrand = map(lambda model: model["name"], brand)
            supportedModels.extend(modelsForBrand)
        
        return supportedModels
       
    def isCameraSupported(self, cameraInfo):
        try:
            self.supportedModels.index(cameraInfo["model"])
            return True
        except ValueError:
            return False
        
    def doCamerasMatch(self, cameraInfos):
        if len(cameraInfos) == 2 and cameraInfos[0]["model"] == cameraInfos[1]["model"]:
            return True
        
        return False
        
    def status(self):            
        cameraStatus = {
            "supportedCameras": self.cameraSupportConfig["supportedCameras"]
        }
        connectedCameras = self.cameraInfo()
        
        # No cameras
        if len(connectedCameras) is 0:
            cameraStatus["status"] = "noCameras"
            return cameraStatus
        
        # One camera
        if len(connectedCameras) is 1:
            if self.isCameraSupported(connectedCameras[0]) is True:
                cameraStatus["status"] = "oneCameraCompatible"
            else:
                cameraStatus["status"] = "oneCameraIncompatible"
            return cameraStatus
        
        # Multiple cameras
        if self.cameraSupportConfig["allowUnsupportedCameras"] is True:
            cameraStatus["status"] = "success"
            return cameraStatus
        
        # Two unmatching cameras
        if self.doCamerasMatch(connectedCameras) is False:
            leftSupported = self.isCameraSupported(connectedCameras[0])
            rightSupported = self.isCameraSupported(connectedCameras[1])
            
            if leftSupported and rightSupported:
                cameraStatus["status"] = "notMatchingCompatible"
            elif leftSupported is False and rightSupported is False:
                cameraStatus["status"] = "notMatchingIncompatible"
            else:
                cameraStatus["status"] = "notMatchingOneCompatibleOneNot"
            return cameraStatus
        
        # Two matching cameras
        if self.isCameraSupported(connectedCameras[0]):
            cameraStatus["status"] = "success"
        else:
            cameraStatus["status"] = "incompatible"
        return cameraStatus

    def generateImageName(self):
        self.imageIndex += 1     
        return "%s%04d.jpg" % (imagePrefix, self.imageIndex)
    
    def capture(self, port, imageFilePath):        
        # Capture the image using gPhoto
        # TODO: Move this out of code and into configuration
        captureCmd = [
            "gphoto2",
            "--capture-image-and-download",
            "--force-overwrite",
            "--port=%s" % port,
            "--filename=%s" % imageFilePath
        ]
        utils.invokeCommandSync(captureCmd, CaptureError, \
                                "Could not capture an image with the camera connected on port %s" \
                                % port)
        return imageFilePath
    
    def capturePage(self, port):
        imageFileName = self.generateImageName()
        imagePath = CAPTURE_DIR + imageFileName
        self.capture(port, self.resources.filePath(imagePath))
        return imagePath
    
    def capturePageSpread(self):
        connectedCameras = self.cameraInfo()
        if len(connectedCameras) < 2:
            raise CaptureError, "Two connected cameras were not detected."
        firstImage = self.capturePage(connectedCameras[0]["port"])
        secondImage = self.capturePage(connectedCameras[1]["port"])
        return firstImage, secondImage

    def captureCalibrationImage(self, cameraName):
        serialNumber = self.calibrationModel()[cameraName]["id"]
        port = self.serialNumberPortMap[serialNumber]
        
        # Check if the camera is still connected to the port we last saw it on
        cameraInfo = self.cameraInfo()
        foundCamera = None
        for camera in cameraInfo:
            if camera["port"] == port:
                foundCamera = camera
                break
        
        if foundCamera is None:
            # Recheck the serial numbers and update the cache
            # TODO: Fix this nonsense
            self.serialNumbers()
            port = self.serialNumberPortMap[serialNumber]
        
        # TODO: Throw a specific error here if we can't find the camera anymore.
        
        imagePath = CALIBRATION_DIR + cameraName + "Calibration.jpg"
        self.capture(port, self.resources.filePath(imagePath))
        return imagePath
    
    def captureLeftCalibrationImage(self):
        return captureCalibrationImage("left")
    
    def captureRightCalibrationImage(self):
        return captureCalibrationImage("right")

        
class MockCameras(Cameras):
    
    connectedCameras = None
    
    def __init__(self, resourceSource, cameraConfig, connectedCameras = None):
        Cameras.__init__(self, resourceSource, cameraConfig)
        self.connectedCameras = connectedCameras
        
    def serialNumbers(self):
        cameraInfo = self.cameraInfo()
        first = ("abc", cameraInfo[0])
        second = ("xyz", cameraInfo[1])
        self.serialNumberPortMap = dict([first, second])
        return first[0], second[0]
    
    def cameraInfo(self):
        if self.connectedCameras != None:
            return self.connectedCameras
        
        return [{
            "model": "Canon PowerShot G10",
            "port": "usb:003,004", 
            "capture": True, 
            "download": True
        },{
           "model": "Canon PowerShot G10", 
           "port": "usb:002,012", 
           "capture": True, 
           "download": True
        }]
    
    def capture(self, camera, imageFileName):
        """Copies an image from the mock images folder to the specified image file path."""        

        files = glob.glob(self.resources.filePath("${mockImages}/*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[self.imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(imageFileName)
        
        return imageFileName
