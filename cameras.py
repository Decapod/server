import os
import glob
from PIL import Image
import simplejson as json

captureDir = "${capturedImages}/"
imagePrefix = "decapod-"

class CaptureError(Exception): pass

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
        
        # Create the captured images directory if needed.
        if os.path.exists(self.resources.filePath("${capturedImages}")) == False:
            os.mkdir(self.resources.filePath("${capturedImages}"))

    def cameraInfo(self):
        # TODO: Make this real!
       return [{
            "model": "Canon PowerShot G10",
            "port": "usb:001,014",
            "capture": True, 
            "download": True
         },
         {
            "model": "Canon PowerShot G10",
            "port": "usb:001,015", 
            "capture": True, 
            "download": True
         }]

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
        status = os.system(("gphoto2 --capture-image-and-download" + \
                           " --force-overwrite --port=%s --camera='%s'" + \
                           " --filename=%s 2>>capture.log") % (port, model, fullImagePath))
        if status != 0:
            raise CaptureError, "Camera could not capture."

        return imagePath
    
    def captureImagePair(self):
        detectedCameras = self.cameraInfo()
        return self.captureImage(detectedCameras[0]), \
               self.captureImage(detectedCameras[1])


class MockCameras(Cameras):
    
    def cameraInfo(self):
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

