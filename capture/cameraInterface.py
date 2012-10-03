from __future__ import division
import os
import sys
import math
import time
from PIL import Image
from string import Template

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

# The camera status are checked in the listed order
CAMERA_STATUS = {
    "NO_CAMERAS": "No cameras detected", 
    "CAMERA_DISCONNECTED": "A Camera has been disconnected",
    "NO_CAPTURE": "Could not capture an image",
    "TOO_MANY_CAMERAS": "Too many cameras detected",
    "READY": "Ready"
}

'''
A global variable to indicate if the simultaneous capture has been prepared
'''
multiCamerasPrepared = False

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
    
    if multiCamerasPrepared:
        releaseCameras()
        
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
    
    if multiCamerasPrepared:
        releaseCameras()
        
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
        
        actualFileLocation = utils.image.renameWithExtension(fileLocation)
        
        return actualFileLocation
    else:
        raise InvalidPortError

def multiCapture(multiCaptureFuncName, cameraPorts, captureNameTemplate, captureDir=DEFAULT_TEMP_DIR, delay=DEFAULT_DELAY, interval=DEFAULT_INTERVAL):
    trackedMultiCaptureFunc = multiCaptureFuncName
    
    multiCaptureFunc = utils.conversion.convertStrToFunc(sys.modules[__name__], multiCaptureFuncName)

    try:
        fileLocations = multiCaptureFunc(ports=cameraPorts, 
                                     filenameTemplate=captureNameTemplate, 
                                     dir=captureDir, 
                                     delay=delay,
                                     interval=interval)
    except TimeoutError as e:
        # Fall back to sequential capture
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
    
    fileLocations = []
    
    try:
        for camera, port in enumerate(ports):
            filename = Template(filenameTemplate).safe_substitute(cameraID=camera)
            fileLocations.append(capture(port, filename, dir))
    except Exception:
        for fileLocation in fileLocations:
                os.remove(fileLocation)
        raise CaptureError("Cannot complete sequential captures.")
        
    return fileLocations

'''
Global list variables to save the locations of temporary and actual files used by multi camera capture
'''
tempCaptureLocations = []

def simultaneousCapture(**kwargs):
    '''
    Takes a picture with the cameras at each of the specified ports in order.
    Can take in a filenameTemplate to be used for naming the captured images. "${cameraID}" will be replaced by a number representing the camera.
    Can also specify a directory where the images should be stored to.
    
    Retuns a list of paths to the captured images.
    If there is an exception during capture it will attempt to remove all of the successful captures. However, any created directory structure will remain in place.
    '''
    actualCaptureLocations = []

    ports = kwargs["ports"]
    filenameTemplate = kwargs["filenameTemplate"]
    dir = kwargs["dir"]
    tempDir = kwargs.get("tempDir", DEFAULT_TEMP_DIR)
    delay = kwargs.get("delay", DEFAULT_DELAY)
    interval = kwargs("interval", DEFAULT_INTERVAL)
    
    global multiCamerasPrepared, tempCaptureLocations
    
    for port in ports:
        if (not isPortValid(port)):
            raise InvalidPortError
    
    try:
        utils.io.makeDirs(tempDir)
    except Exception:
        raise IOError("Cannot create directory {0}".format(tempDir))
    
    try:
        utils.io.makeDirs(dir)
    except Exception:
        raise IOError("Cannot create directory {0}".format(dir))
    
    try:
        if not multiCamerasPrepared:
            # Prepare the cameras for the simultaneous capture. Only run once.
            for camera, port in enumerate(ports):
                tempFileLocation = os.path.join(tempDir, str(camera))
                tempCaptureLocations.append(tempFileLocation)
                
                cmd = [
                    "gphoto2",
                    "--capture-image-and-download",
                    "--force-overwrite",
                    "--port={0}".format(port),
                    "--filename={0}".format(tempFileLocation),
                    "-I -1"
                ]
                
                captureInfo = utils.io.invokeCommandSync(cmd, None, None, False)
            
            multiCamerasPrepared = True
        else:
            # Subsequent simultaneous captures after the preparation by sending USR1 signal to gphoto2
            cmd = [
                "killall",
                "-USR1",
                "gphoto2"
            ]
            
            captureInfo = utils.io.invokeCommandSync(cmd,
                                    CaptureError,
                                    "Could not simultaneously capture images from these ports {0}.".format("; ".join(ports)))
            
            # rename
    except Exception:
        for fileLocation in tempCaptureLocations:
            if os.path.exists(fileLocation): 
                os.remove(fileLocation)
        raise
    
    # rename image name to the desired image name
    for camera, tempFile in enumerate(tempCaptureLocations):
        actualCaptureLocation = os.path.join(dir, Template(filenameTemplate).safe_substitute(cameraID=camera))
        try:
            if fileCreated(tempFile, delay, interval):
                os.rename(tempFile, actualCaptureLocation)
        except TimeoutError:
            for fileLocation in tempCaptureLocations[camera:]:
                if os.path.exists(fileLocation): os.remove(fileLocation)
            for fileLocation in actualCaptureLocations:
                if os.path.exists(fileLocation): os.remove(fileLocation)
            raise TimeoutError("Could not simultaneously capture images.")
            
        actualCaptureLocation = utils.image.renameWithExtension(actualCaptureLocation)
        
        actualCaptureLocations.append(actualCaptureLocation)
        
    return actualCaptureLocations

def fileCreated(fileLocation, delay, interval):
    '''
    Check if the request file is created during a time frame, defined by "delay". Check the file existence every given interval.
    Return true if the file is created. Raise a timeout error if the file is NOT created in the time frame.
    '''
    currentDelay = 0
    
    while True:
        time.sleep(interval)
        currentDelay = currentDelay + interval
        
        if os.path.exists(fileLocation):
            return True
        if currentDelay >= delay:
            raise TimeoutError
            break
    
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

def releaseCameras():
    '''
    Kill all gphoto2 threads to release all the connected cameras in case they have been prepared for simultaneous captures.
    '''
    cmd = [
        "killall",
        "gphoto2"
    ]
    
    try:
        captureInfo = utils.io.invokeCommandSync(cmd,
                                CaptureError,
                                "Could not release cameras.")
    except Exception:
        return False
    
    return True

def generateCameraStatus(statusCode, **kwargs):
    '''
    Generates a dictionary with the camera status info.
    Can pass in keyword arguements for addiontal info to add to the dictionary
    '''
    statusInfo = {
        "statusCode": statusCode,
        "message": CAMERA_STATUS[statusCode]
    }
    statusInfo.update(kwargs)
    return statusInfo
