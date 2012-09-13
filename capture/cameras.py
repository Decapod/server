from __future__ import division
import os
import sys
from PIL import Image
import math

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import utils

class DetectCamerasError(Exception): pass
class InvalidPortError(Exception): pass
class CaptureError(Exception): pass

def parseCamerasInfo(info):
    infoList = []
    
    allInfo = info.split('\n')
    
    # Get rid of the useless header and footer from the gphoto2 return
    infoInLines = allInfo[2:-1]
    
    if (len(infoInLines) == 0): return infoList
    
    # Slice the camera info by using the location of 'Port' string in header
    slicePos = allInfo[0].index('Port')
    
    for line in infoInLines:
        model = line[0:slicePos - 1].strip()
        port = line[slicePos:].strip()
        infoList.append({'model': model, 'port': port})
    
    return infoList

def detectCameras():
    cmd = [
        "gphoto2",
        "--auto-detect"
    ]
    
    camerasInfo = utils.io.invokeCommandSync(cmd,
                            DetectCamerasError,
                            "Could not detect cameras.")
    
    return parseCamerasInfo(camerasInfo)
#cameras.detectCameras()    

def isPortValid(port):
    '''
    Check if the given port has a camera connected
    '''
    # make sure the given port is valid
    connectedCameras = detectCameras()
    
    for camera in connectedCameras:
        if (camera['port'] == port): return True

    return False

def getCameraSummary(port):
    '''
    Return the summary information of the camera that's connected to the given port
    '''
    cameraInfo = {}
    
    #cameras.getCameraSummary("usb:001,010")
    if (isPortValid(port)):
        cmd = [
            "gphoto2",
            "--summary",
            "--port={0}".format(port)
        ]
        
        cameraInfo = utils.io.invokeCommandSync(cmd,
                                DetectCamerasError,
                                "Could not get the camera summary.")
        
        return cameraInfo

    return cameraInfo

def capture(port, filename, dir='images'):
    '''
    Take a picture with the given name into the given directory, and return the path to the picture
    '''
    
    fileLocation = os.path.join(dir, filename)
    
    if (isPortValid(port)):
        cmd = [
            "gphoto2",
            "--capture-image-and-download",
            "--force-overwrite",
            "--port={0}".format(port),
            "--filename={0}".format(fileLocation)
        ]
        
        captureInfo = utils.io.invokeCommandSync(cmd,
                                CaptureError,
                                "Could not capture an images from port {0}.".format(port))
        
        return fileLocation
    else:
        raise InvalidPortError

def getResolution(port):
    '''
    Calculate and return the camera's resolution by taking a test picture and 
    '''
    imageName = utils.image.generateImageName()
    
    capture(port, imageName, '')
    
    img = Image.open(imageName)
    width, height = img.size
    
    os.remove(imageName)

    return round((width * height) / 1000000, 1)