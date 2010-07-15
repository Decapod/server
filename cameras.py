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
    calibrationModel = None
    
    def __init__(self, resourceSource, cameraConfig):
        self.resources = resourceSource
        
        # Load the supported cameras configuration.
        supportedCamerasPath = self.resources.filePath(cameraConfig)
        supportedCamerasJSON = open(supportedCamerasPath)
        self.cameraSupportConfig = json.load(supportedCamerasJSON)
        self.supportedModels = self.mapSupportedCamerasToModelList()

        # Setup the calibration model.
        self.calibrationModel = self.defaultCalibrationModel()
                
        # Setup the capture locations.
        utils.mkdirIfNecessary(self.resources.filePath(CAPTURE_DIR))
        utils.remakeDir(self.resources.filePath(CALIBRATION_DIR))

    def defaultCalibrationModel(self):
        # TODO: Use a better scheme for keeping track of left and right cameras.
        ports = self.cameraPortsAscending()
        calibration = {
            "left": {
                "id": ports[0],
                "rotation": 0
            },
            "right": {
                "id": ports[1],
                "rotation": 0
            }                
        }
        return calibration
    
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
    
    def capture(self, camera, imageFilePath):
        port = camera["port"]
        model = camera["model"]
        
        # Capture the image using gPhoto
        # TODO: Move this out of code and into configuration
        captureCmd = [
            "gphoto2",
            "--capture-image-and-download",
            "--force-overwrite",
            "--camera='%s'" % model,
            "--port=%s" % port,
            "--filename=%s" % imageFilePath
        ]
        utils.invokeCommandSync(captureCmd, CaptureError, \
                                "Could not capture an image with the camera %s on port %s" \
                                % (model, port))
        return imageFilePath
    
    def capturePage(self, camera):
        imageFileName = self.generateImageName()
        imagePath = CAPTURE_DIR + imageFileName
        self.capture(camera, self.resources.filePath(imagePath))
        return imagePath
    
    def capturePageSpread(self):
        connectedCameras = self.cameraInfo()
        if len(connectedCameras) < 2:
            raise CaptureError, "Two connected cameras were not detected."
        firstImage, secondImage = self.capturePage(connectedCameras[0]), self.capturePage(connectedCameras[1])
        return firstImage, secondImage

    def captureCalibrationImage(self, cameraName):
        cameraID = self.calibrationModel[cameraName]["id"]
        connectedCameras = self.cameraInfo()
        cameraWithID = None
        for camera in connectedCameras:
            if camera["port"] is cameraID:
                cameraWithID = camera
        
        imagePath = CALIBRATION_DIR + cameraName + "Calibration.jpg"
        self.capture(camera, self.resources.filePath(imagePath))
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
