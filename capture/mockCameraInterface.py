from __future__ import division
import os
import sys
import shutil
from string import Template

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import utils

class InvalidPortError(Exception): pass

CAMERA_INFO_BY_PORT = {
    "usb:001,002": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture",
        "capture": "../mockData/images/1.jpg"
    },
    "usb:001,003": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture",
        "capture": "../mockData/images/2.jpg"
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
    
def multiCameraCapture(ports, filenameTemplate="capture$cameraID", dir="images"):
    fileLocations = []
    
    try:
        for camera, port in enumerate(ports):
            filename = Template(filenameTemplate).safe_substitute(cameraID=camera)
            fileLocations.append(capture(port, filename, dir))
    except Exception:
        for fileLocation in fileLocations:
                os.remove(fileLocation)
        raise
        
    return fileLocations

def getResolution(port):
    return CAMERA_INFO_BY_PORT[port]["resolution"]