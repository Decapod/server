import sys
import os
import glob
from PIL import Image
import unittest

import testutils
sys.path.append(os.path.abspath('..'))
import cameras

RIGHT_CAMERA_PORT = "usb:003,004"

class CamerasTest(unittest.TestCase):

    resources = None
    
    otherConnectedCameras = [{
        "model": "Canon PowerShot G10",
        "port": "usb:999,999",
        "id": "foo"
    }, {
        "model": "Nikon D90",
        "port": "usb:000,001",
        "id": "ni!"
    }]
    
    expectedSupportedCameras = {
        "Canon": [{
            "name": "Canon PowerShot G10",
            "label": "PowerShot G10"
        }],
        "Nikon": [{
            "name": "Nikon D90",
            "label": "D90"
        }]
    }
    expectedDefaultCalibrationModel = {
        "left": {
            "id": "xyz",
            "rotation": 0
        },
        "right": {
            "id": "abc",
            "rotation": 0
        }
    }
    
    def createCameras(self, connectedCameras = None):
        cams = cameras.MockCameras(self.resources,
                                   "${testData}/supported-cameras-test-data.json", 
                                   connectedCameras)
        return cams
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()
        
    def tearDown(self):
        testutils.cleanUpCapturedImages()
        testutils.cleanUpDir(self.resources.filePath("${calibrationImages}"))
        
    def test_refreshConnectedCameras(self):
        cams = self.createCameras()
        self.assertEquals(cams.calibrationModel, self.expectedDefaultCalibrationModel);
        
        # Now try with no cameras connected.
        cams = self.createCameras([])
        cams.refreshCalibrationModel()
        self.assertEquals([], cams.calibrationModel)

        cams.connectedCameras = self.otherConnectedCameras
        cams.refreshConnectedCameras()
        self.assertEquals(cams.calibrationModel, {
            "left": {
                "id": "ni!",
                "rotation": 0
            },
            "right": {
                "id": "foo",
                "rotation": 0
            }
        })
        
    def checkCameraStatus(self, expectedStatus, connectedCameras):
        cams = self.createCameras(connectedCameras)
        status = cams.status()
        self.assertEquals(status,{
            "status": expectedStatus,
            "supportedCameras": self.expectedSupportedCameras
        })
        
    def test_status(self):
        # No cameras
        self.checkCameraStatus("noCameras", [])

        # One supported camera
        self.checkCameraStatus("oneCameraCompatible", [{
            "model": "Canon PowerShot G10",
            "id": "abc",
            "port": "usb:x,y"
        }])
        
        # One unsupported camera
        self.checkCameraStatus("oneCameraIncompatible", [{
            "model": "Cat Camera",
            "id": "abc",
            "port": "usb:x,y"
        }])
        
        # Two supported, unmatching cameras
        self.checkCameraStatus("notMatchingCompatible", [{
            "model": "Canon PowerShot G10",
            "id": "abc",
            "port": "usb:x,y"
        }, {
            "model": "Nikon D90",
            "id": "def",
            "port": "usb:x,y"
        }])
        
        # Two unmatched cameras, one unsupported
        self.checkCameraStatus("notMatchingOneCompatibleOneNot", [{
            "model": "Cat Camera",
            "id": "abc",
            "port": "usb:x,y"
        }, {
            "model": "Nikon D90",
            "id": "def",
            "port": "usb:x,y"
        }])
        
        # Two unmatched cameras, neither supported
        self.checkCameraStatus("notMatchingIncompatible", [{
            "model": "Cat Camera",
            "id": "abc",
            "port": "usb:x,y"
        }, {
            "model": "Commodore 64",
            "id": "def",
            "port": "usb:x,y"
        }])
        
        # Two matching, unsupported cameras
        self.checkCameraStatus("incompatible", [{
            "model": "Cat Camera",
            "id": "abc",
            "port": "usb:x,y"
        }, {
            "model": "Cat Camera",
            "id": "def",
            "port": "usb:x,y"
        }])
        
        # Two matching, supported cameras
        self.checkCameraStatus("success", [{
            "model": "Nikon D90",
            "id": "abc",            
            "port": "usb:x,y"
        }, {
            "model": "Nikon D90",
            "id": "def",
            "port": "usb:x,y"
        }])
        
    def test_capture(self):
        cams = self.createCameras()
        imagePath = self.resources.filePath(cameras.CAPTURE_DIR + "test-capture.jpg")
        cams.capture(RIGHT_CAMERA_PORT, imagePath)
        self.assertTrue(os.path.exists(imagePath))
    
    def setCameraRotation(self, cams, rotation, camera):
        calModel = cams.calibrationModel
        calModel[camera]["rotation"] = rotation
        cams.calibrationModel = calModel
        
    def checkCapturedImage(self, cams, cameraName, expectedSize):
        result = cams.capturePage(cameraName)
        absResult = self.resources.filePath(result)
        self.assertTrue(os.path.exists(absResult))
        im = Image.open(absResult)
        self.assertEquals(expectedSize, im.size)
        
    def test_capturePage(self):
        # Default calibration--no rotation
        cams = self.createCameras()
        expectedSize = (450, 600)
        self.checkCapturedImage(cams, "right", expectedSize)
        
        # Captured with calibration of 90 rotation specified
        cams = self.createCameras()
        self.setCameraRotation(cams, 90, "right")
        expectedSize = (600, 450)
        self.checkCapturedImage(cams, "right", expectedSize)
        
    def checkCalibrationImage(self, cams, cameraName):
        calibrationImagePath = cams.captureCalibrationImage(cameraName)
        self.assertTrue(os.path.exists(self.resources.filePath(calibrationImagePath)))
        
    def checkCalibrationPair(self, cams):
        self.checkCalibrationImage(cams, "right")
        self.checkCalibrationImage(cams, "left")
        self.assertEquals(2, len(glob.glob(self.resources.filePath(cameras.CALIBRATION_DIR) + "/*")))
        
    def test_captureCalibrationImage(self):
        cams = self.createCameras()
        
        # Check both left and right captures.
        self.checkCalibrationPair(cams)
        
        # Now try them again.
        self.checkCalibrationPair(cams)
        
        # Try a camera that doesn't exist
        calibrationImagePath = None
        try:
            calibrationImagePath = cams.captureCalibrationImage("hotdog")
            self.fail("Capturing a calibration image with an invalid camera should result in an exception")
        except cameras.CameraError:
            self.assertTrue(calibrationImagePath is None)

        