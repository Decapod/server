from __future__ import division
import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import utils

class InvalidPortError(Exception): pass

CAMERA_INFO_BY_PORT = {
    "usb:001,002": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture"
    },
    "usb:001,003": {
        "model": "Canon PowerShot G10",
        "captureFormats": "JPEG",
        "resolution": 14.6,
        "capabilities": "File Download, File Deletion, File Upload\n\tGeneric Image Capture, No Open Capture, Canon Capture"
    }
};

def detectCameras():
    cameras = []
    
    for port in CAMERA_INFO_BY_PORT:
        cameras.append({"model": CAMERA_INFO_BY_PORT[port]["model"], "port": port})

    return cameras

def isPortValid(port):
    return port in CAMERA_INFO_BY_PORT

def arePortsValid(ports):
    for port in ports:
        if not isPortValid(port): return False
    
    return True
    
def getCameraSummaryByPort(port):
    summary = {}
    
    if (isPortValid(port)):
        summary = CAMERA_INFO_BY_PORT[port]

    return summary

def getAllCamerasSummary():
    allInfo = {}
    allInfo["cameras"] = []
    
    connectedCameras = detectCameras()
    
    for camera in connectedCameras:
        allInfo['cameras'].append(getCameraSummaryByPort(camera["port"]))
    
    return allInfo

def capture(port, filename, dir="images"):
    '''
    Not yet implemented
    '''
    if (isPortValid(port)):
        return None
    else: 
        raise InvalidPortError
    
def multiCameraCapture(ports, filenameTemplate="capture{0}", dir="images"):
    '''
    Not yet implemented
    '''
    if not arePortsValid(ports): raise InvalidPortError

def getResolution(port):
    return CAMERA_INFO_BY_PORT[port]["resolution"]