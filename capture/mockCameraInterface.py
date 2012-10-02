from __future__ import division
import os
import sys
import shutil
from string import Template

import cameraInterface
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import utils

class DetectCamerasError(Exception): pass
class InvalidPortError(Exception): pass
class CaptureError(Exception): pass
class GetResolutionError(Exception): pass
class TimeoutError(Exception): pass
class MultiCaptureError(Exception): pass

DEFAULT_TEMP_DIR = "temp"
DEFAULT_DELAY = 10
DEFAULT_INTERVAL = 0.5

CAMERA_INFO_BY_PORT = {
    "usb:001,002": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture",
        "capture": "mockData/images/capture-0_1.jpg"
    },
    "usb:001,003": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture",
        "capture": "mockData/images/capture-0_2.jpg"
    }
};

def detectCameras():
    cameras = []
    
    for port in CAMERA_INFO_BY_PORT:
        cameras.append({"model": CAMERA_INFO_BY_PORT[port]["model"], "port": port})

    return cameras

def getPorts():
    return CAMERA_INFO_BY_PORT.keys()

def isPortValid(port):
    return port in CAMERA_INFO_BY_PORT

def getCameraSummaryByPort(port):
    keysToRemove = ["capture"]
    summary = {}
    
    if (isPortValid(port)):
        summary = CAMERA_INFO_BY_PORT[port].copy()
        # removes the camera info that shouldn't be included in the summary.
        for key in keysToRemove:
            if key in summary:
                del summary[key]

    return summary

def getAllCamerasSummary():
    allInfo = {}
    allInfo["cameras"] = []
    
    connectedCameras = detectCameras()
    
    for camera in connectedCameras:
        allInfo['cameras'].append(getCameraSummaryByPort(camera["port"]))
    
    return allInfo

def capture(port, filename, dir="images"):
    if (isPortValid(port)):
        utils.io.makeDirs(dir);
        fileLocation = os.path.join(dir, filename)
        shutil.copyfile(CAMERA_INFO_BY_PORT[port]["capture"], fileLocation)
        return fileLocation
    else: 
        raise InvalidPortError
    
def multiCapture(multiCaptureFuncName, cameraPorts, captureNameTemplate, captureDir, delay, interval):
    trackedMultiCaptureFunc = multiCaptureFuncName
    
    multiCaptureFunc = utils.conversion.convertStrToFunc(sys.modules[__name__], multiCaptureFuncName)

    try:
        fileLocations = multiCaptureFunc(ports=cameraPorts, 
                                     filenameTemplate=captureNameTemplate, 
                                     dir=captureDir, 
                                     delay=delay,
                                     interval=interval)
    except TimeoutError as e:
        # TODO: fall back to sequential capture
        if len(cameraPorts) > 0:
            releaseCameras()
        
        trackedMultiCaptureFunc = "sequentialCapture"
        
        multiCaptureFunc = utils.conversion.convertStrToFunc(sys.modules[__name__], trackedMultiCaptureFunc)
        
        try:
            fileLocations = multiCaptureFunc(ports=cameraPorts, 
                                         filenameTemplate=captureNameTemplate, 
                                         dir=captureDir)
        except CaptureError as e:
            raise MultiCaptureError(e.message)
        
    except CaptureError as e:
        raise MultiCaptureError(e.message)
    
    return fileLocations, trackedMultiCaptureFunc

def implMultiCapture(ports, filenameTemplate, dir):
    fileLocations = []

    try:
        for camera, port in enumerate(ports):
            filename = Template(filenameTemplate).safe_substitute(cameraID=camera)
            capturedFile = capture(port, filename, dir)
            
            fileLocations.append(utils.image.renameWithExtension(capturedFile))
    except Exception:
        for fileLocation in fileLocations:
                os.remove(fileLocation)
        raise
        
    return fileLocations

def sequentialCapture(**kwargs):
    
    '''
    Takes a picture with the cameras at each of the specified ports in order.
    Can take in a filenameTemplate to be used for naming the captured images. "$cameraID" will be replaced by a number representing the camera.
    Can also specify a directory where the images should be stored to.
    
    Retuns a list of paths to the captured images.
    If there is an exception during capture it will attempt to remove all of the successful captures. However, any created directory structure will remain in place.
    '''
    ports = kwargs["ports"]
    filenameTemplate = kwargs["filenameTemplate"]
    dir = kwargs["dir"]
    
    return implMultiCapture(ports, filenameTemplate, dir)
    
def simultaneousCapture(**kwargs):
    ports = kwargs["ports"]
    filenameTemplate = kwargs["filenameTemplate"]
    dir = kwargs["dir"]
    tempDir = kwargs["tempDir"] if kwargs.has_key("tempDir") else DEFAULT_TEMP_DIR
    delay = kwargs["delay"] if kwargs["delay"] else DEFAULT_DELAY
    interval = kwargs["interval"] if kwargs.has_key("interval") else DEFAULT_INTERVAL
    
    return implMultiCapture(ports, filenameTemplate, dir)
    
def getResolution(port):
    return CAMERA_INFO_BY_PORT[port]["resolution"]

def releaseCameras():
    return True

def raiseTimeoutError(**kwargs):
    raise TimeoutError

def generateCameraStatus(statusCode, **kwargs):
    return cameraInterface.generateCameraStatus(statusCode, **kwargs)