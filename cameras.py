import os
import glob
import subprocess
from PIL import Image
import simplejson as json
import decapod_utilities as utils

captureDir = "${capturedImages}/"
imagePrefix = "decapod-"

class CameraError(Exception): pass
class CaptureError(CameraError): pass

class Cameras(object):
    
    imageIndex = 0;
    supportedCameras = None
    resources = None
    
    def __init__(self, resourceSource, cameraConfig):
        self.resources = resourceSource
        
        # Load the supported cameras configuration.
        supportedCamerasPath = self.resources.filePath(cameraConfig)
        supportedCamerasJSON = open(supportedCamerasPath)
        self.supportedCameras = json.load(supportedCamerasJSON)
        
        utils.mkdirIfNecessary(self.resources.filePath(captureDir))


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
    
    def status(self):
        return {
            "status": "Awesome",
            "supportedCameras": self.supportedCameras
        }

    def generateImageName(self):
        self.imageIndex += 1     
        return "%s%04d.jpg" % (imagePrefix, self.imageIndex)
    
    def captureImage(self, camera):
        imageFileName = self.generateImageName()
        imagePath = captureDir + imageFileName
        fullImagePath = self.resources.filePath(imagePath)
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
            "--filename=%s" % fullImagePath
        ]
        utils.invokeCommandSync(captureCmd, CaptureError, \
                                "Could not capture an image with the camera %s on port %s" \
                                % (model, port))
        return imagePath
    
    def captureImagePair(self):
        detectedCameras = self.cameraInfo()
        if len(detectedCameras) < 2:
            raise CaptureError, "Two connected cameras were not detected."
        return self.captureImage(detectedCameras[0]), \
               self.captureImage(detectedCameras[1])


class MockCameras(Cameras):
    
    def cameraInfo(self):
        # TODO: These should be made to match the list of supported cameras.
        return [{
            "model": "Canon Powershot SX110IS", 
            "port": "usb:002,012", 
            "capture": True, 
            "download": True
        },{
           "model": "Nikon D80", 
           "port": "usb:003,004", 
           "capture": True, 
           "download": True
        }]
    
    def captureImage(self, camera):
        """Copies an image from the mock images folder to the captured images folder."""        
        capturedFileName = self.generateImageName()
        capturedFilePath = captureDir + capturedFileName
        
        files = glob.glob(self.resources.filePath("${mockImages}/*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[self.imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(self.resources.filePath(capturedFilePath));
        
        return capturedFilePath

