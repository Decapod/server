import glob
from PIL import Image

class Cameras(object):
    
    supportedCameras = None
    
    def __init__(self, supportedCameras):
        self.supportedCameras = supportedCameras
        
    def cameraInfo(self):
        return None

    def status(self):
        return {
            "status": "Awesome",
            "supportedCameras": self.supportedCameras
        }
        
    def captureImagePair(self):
        return None

# TODO: Address the dependency creep issue where we require a ResourceSource
# only in the mock implementation, which requires awareness of mockiness to float 
# higher up
class MockCameras(Cameras):
    
    imageIndex = 0
    resources = None
    
    def __init__(self, supportedCameras, resourceSource):
        self.resources = resourceSource
        
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
    
    def captureImage(self):
        """Copies an image from the mock images folder to the captured images folder."""        
        capturedFileName = "Image%d.jpg" % (self.imageIndex)
        capturedFilePath = "${capturedImages}/" + capturedFileName
        self.imageIndex = self.imageIndex + 1
        
        files = glob.glob(self.resources.filePath("${mockImages}/*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[self.imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(self.resources.filePath(capturedFilePath));
        
        return capturedFilePath
    
    def captureImagePair(self):
        return self.captureImage(), self.captureImage()
