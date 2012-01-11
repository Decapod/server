import os
import glob
import subprocess
from PIL import Image
import simplejson as json
import decapod_utilities as utils
import imageprocessing

CAPTURE_DIR = "${book}/capturedImages/"
CALIBRATION_DIR = "${calibrationImages}/"
imagePrefix = "decapod-"

class CameraError(Exception): pass
class CaptureError(CameraError): pass


#########################################
# Free camera-related utility functions #
#########################################

def detectCameras():
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
        
        # Tokenize the line on spaces, grab the last token, and assume it's the port
        # Then stitch the rest of the tokens back and assume that they're the model name.
        tokens = cameraInfo.split()
        if len(tokens) < 1:
            continue
        port = tokens.pop()
        camera = {
            "port": port,
            "model": " ".join(tokens),
            "id": serialNumberForPort(port),
            "capture": True, # TODO: Remove this property
            "download": True # TODO: Remove this property
        }
        cameras.append(camera)
        
    return cameras

def serialNumberForPort(port):
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
    

###########
# Cameras #
###########

class Cameras(object):
    
    resources = None
    imageIndex = 0;
    cameraSupportConfig = None
    supportedModels = None
    connectedCameras = []
    calibrationModel = {}

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

        # Setup the camera and calibration models
        self.refreshConnectedCameras()
    
    def refreshConnectedCameras(self):        
        # Detect cameras and update our model.
        self.connectedCameras = detectCameras()
        self.refreshCalibrationModel()
        return self.connectedCameras
    
    def refreshCalibrationModel(self):
        # Set the calibration model to a default if appropriate.
        if (len(self.calibrationModel) > 0):
            return self.calibrationModel
        
        if self.connectedCameras is None or len(self.connectedCameras) < 2:
            self.calibrationModel = []
        else:
            ascendingCameras = sorted(self.connectedCameras, key=lambda camera: camera["port"])
            self.calibrationModel = {
                "left": {
                    "id": ascendingCameras[0]["id"],
                    "rotation": 0
                },
                "right": {
                    "id": ascendingCameras[1]["id"],
                    "rotation": 0
                }
            }
            
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
        self.refreshConnectedCameras()
        
        # No cameras
        if len(self.connectedCameras) is 0:
            cameraStatus["status"] = "noCameras"
            return cameraStatus
        
        # One camera
        if len(self.connectedCameras) is 1:
            if self.isCameraSupported(self.connectedCameras[0]) is True:
                cameraStatus["status"] = "oneCameraCompatible"
            else:
                cameraStatus["status"] = "oneCameraIncompatible"
            return cameraStatus
        
        # Multiple cameras
        if self.cameraSupportConfig["allowUnsupportedCameras"] is True:
            cameraStatus["status"] = "success"
            return cameraStatus
        
        # Two unmatching cameras
        if self.doCamerasMatch(self.connectedCameras) is False:
            leftSupported = self.isCameraSupported(self.connectedCameras[0])
            rightSupported = self.isCameraSupported(self.connectedCameras[1])
            
            if leftSupported and rightSupported:
                cameraStatus["status"] = "notMatchingCompatible"
            elif leftSupported is False and rightSupported is False:
                cameraStatus["status"] = "notMatchingIncompatible"
            else:
                cameraStatus["status"] = "notMatchingOneCompatibleOneNot"
            return cameraStatus
        
        # Two matching cameras
        if self.isCameraSupported(self.connectedCameras[0]):
            cameraStatus["status"] = "success"
        else:
            cameraStatus["status"] = "incompatible"
        return cameraStatus

    def generateImageName(self):
        self.imageIndex += 1     
        return "%s%04d.jpg" % (imagePrefix, self.imageIndex)
    
    def capture(self, port, imageFilePath):        
        # Capture the image using gPhoto
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
    
    def portForCameraID(self, id):
        # Check if the camera is still connected to the port we last saw it on
        for camera in self.connectedCameras:
            if camera["id"] == id:
                return camera["port"]
        return None
    
    def captureImageWithCamera(self, cameraName, imagePath):
        calibration = None
        try:
            calibration = self.calibrationModel[cameraName]
        except KeyError:
            raise CameraError, ("The specified camera (%s) does not exist or is not connected." % cameraName)
        
        port = self.portForCameraID(calibration["id"])
        self.capture(port, self.resources.filePath(imagePath))
        return imagePath
    
    def capturePage(self, cameraName):
        imageFileName = self.generateImageName()
        imagePath = CAPTURE_DIR + imageFileName
        capturedPath = self.captureImageWithCamera(cameraName, imagePath)
        
        # Rotate based on the user's calibration model.
        absRotatedPath = self.resources.filePath(capturedPath)
        rotation = self.calibrationModel[cameraName]["rotation"]
        if rotation is not 0:
            imageprocessing.rotate(absRotatedPath, rotation)
            
        return capturedPath
    
    def capturePageSpread(self):
        if len(self.connectedCameras) < 2:
            raise CaptureError, "Two connected cameras were not detected."

        firstImage = self.capturePage("left")
        secondImage = self.capturePage("right")
        return firstImage, secondImage
    
    def captureCalibrationImage(self, cameraName):
        imagePath = CALIBRATION_DIR + cameraName + "Calibration.jpg"
        return self.captureImageWithCamera(cameraName, imagePath)
    
    def captureLeftCalibrationImage(self):
        return captureCalibrationImage("left")
    
    def captureRightCalibrationImage(self):
        return captureCalibrationImage("right")

        
class MockCameras(Cameras):
    
    connectedCameras = None
    
    def __init__(self, resourceSource, cameraConfig, connectedCameras = None):        
        # Set up the mock connected cameras.
        self.connectedCameras = connectedCameras if connectedCameras is not None else [{
            "model": "Canon PowerShot G10",
            "port": "usb:003,004",
            "id": "abc",
            "capture": True, 
            "download": True
        },{
           "model": "Canon PowerShot G10", 
           "port": "usb:002,012",
           "id": "xyz",
           "capture": True, 
           "download": True
        }]
        
        Cameras.__init__(self, resourceSource, cameraConfig)

    
    def refreshConnectedCameras(self):
        # Stubbed out to do nothing.
        self.refreshCalibrationModel()
        return self.connectedCameras
    
    def capture(self, port, imageFileName):
        """Copies an image from the mock images folder to the specified image file path."""        

        files = glob.glob(self.resources.filePath("${mockImages}/*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[self.imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(imageFileName)
        
        return imageFileName
