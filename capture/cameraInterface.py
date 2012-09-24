from __future__ import division
import os
import sys
from PIL import Image
import math
from string import Template

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import utils

class DetectCamerasError(Exception): pass
class InvalidPortError(Exception): pass
class CaptureError(Exception): pass
class GetResolutionError(Exception): pass

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

def getPorts():
    '''
    Return an array of all the ports that have camera connected
    '''
    ports = []
    
    connectedCameras = detectCameras()
    
    for camera in connectedCameras:
        ports.append(camera['port'])
    
    return ports

def isPortValid(port):
    '''
    Check if the given port has a camera connected
    '''
    # make sure the given port is valid
    return port in getPorts()

def getInfo(summaryStr, startKeyword, endKeyword='\n'):
    '''
    Extract capture formats information from the camera summary string
    '''
    
    removedFront = summaryStr[summaryStr.index(startKeyword) + len(startKeyword):]
    return removedFront[0:removedFront.index(endKeyword)].strip()
    
def getCameraSummaryByPort(port):
    '''
    Return the summary information of the camera that's connected to the given port
    '''
    summary = {}
    
    #cameras.getCameraSummary("usb:001,010")
    if (isPortValid(port)):
        cmd = [
            "gphoto2",
            "--summary",
            "--port={0}".format(port)
        ]
        
        summaryStr = utils.io.invokeCommandSync(cmd,
                                DetectCamerasError,
                                "Could not get the camera summary.")
        
        summary['port'] = port
        summary['resolution'] = getResolution(port)
        summary['captureFormats'] = getInfo(summaryStr, 'Capture Formats: ')   
        summary['model'] = getInfo(summaryStr, 'Model: ')
        summary['capabilities'] = getInfo(summaryStr, 'Device Capabilities:', 'Storage Devices Summary:')

    return summary

def getAllCamerasSummary():
    allInfo = {}
    allInfo['cameras'] = []
    
    connectedCameras = detectCameras()
    
    for camera in connectedCameras:
        allInfo['cameras'].append(getCameraSummaryByPort(camera['port']))
    
    return allInfo

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
                                "Could not capture an image from port {0}.".format(port))
        
        return fileLocation
    else:
        raise InvalidPortError

def multiCameraCapture(ports, filenameTemplate="capture$cameraID", dir="images"):
    '''
    Takes a picture with the cameras at each of the specified ports in order.
    Can take in a filenameTemplate to be used for naming the captured images. "$cameraID" will be replaced by a number representing the camera.
    Can also specify a directory where the images should be stored to.
    
    Retuns a list of paths to the captured images.
    If there is an exception during capture it will attempt to remove all of the successful captures. However, any created directory structure will remain in place.
    '''
    fileLocations = []
    
    try:
        for camera, port in enumerate(ports):
            filename = Template(filenameTemplate).safe_substitute(cameraID=camera)
#            filename = filenameTemplate.format(index)
            fileLocations.append(capture(port, filename, dir))
    except Exception:
        for fileLocation in fileLocations:
                os.remove(fileLocation)
        raise
        
    return fileLocations
        

def getResolution(port):
    '''
    Calculate and return the camera's resolution by taking a test picture and 
    '''
    imageName = utils.image.generateImageName()
    
    try:
        capture(port, imageName, '')
    except CaptureError:
        raise GetResolutionError("Could not get resolution: Error at capturing a test image from port {0}.".format(port))
    
    img = Image.open(imageName)
    width, height = img.size
    
    os.remove(imageName)

    return round((width * height) / 1000000, 1)