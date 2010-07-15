import sys
import os
import unittest
import testutils

sys.path.append(os.path.abspath('..'))
import cameras

class CamerasTest(unittest.TestCase):

    resources = None
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
            "id": "abc",
            "rotation": 0
        },
        "right": {
            "id": "xyz",
            "rotation": 0
        }
    }
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()

    def tearDown(self):
        testutils.cleanUpCapturedImages()
        
    def test_defaultCalibrationModel(self):
        cams = cameras.MockCameras(self.resources,
                                           "${testData}/supported-cameras-test-data.json")
        calibration = cams.calibrationModel()
        self.assertEquals(calibration, self.expectedDefaultCalibrationModel);
        
    def checkCameraInfo(self, expectedStatus, connectedCameras):
        cams = cameras.MockCameras(self.resources, 
                                   "${testData}/supported-cameras-test-data.json", 
                                   connectedCameras)
        status = cams.status()
        self.assertEquals(status,{
            "status": expectedStatus,
            "supportedCameras": self.expectedSupportedCameras
        })
        
    def test_status(self):
        # No cameras
        self.checkCameraInfo("noCameras", [])

        # One supported camera
        self.checkCameraInfo("oneCameraCompatible", [{
            "model": "Canon PowerShot G10"
        }])
        
        # One unsupported camera
        self.checkCameraInfo("oneCameraIncompatible", [{
            "model": "Cat Camera"
        }])
        
        # Two supported, unmatching cameras
        self.checkCameraInfo("notMatchingCompatible", [{
            "model": "Canon PowerShot G10"
        }, {
            "model": "Nikon D90"
        }])
        
        # Two unmatched cameras, one unsupported
        self.checkCameraInfo("notMatchingOneCompatibleOneNot", [{
            "model": "Cat Camera"
        }, {
            "model": "Nikon D90"
        }])
        
        # Two unmatched cameras, neither supported
        self.checkCameraInfo("notMatchingIncompatible", [{
            "model": "Cat Camera"
        }, {
            "model": "Commodore 64"
        }])
        
        # Two matching, unsupported cameras
        self.checkCameraInfo("incompatible", [{
            "model": "Cat Camera"
        }, {
            "model": "Cat Camera"
        }])
        
        # Two matching, supported cameras
        self.checkCameraInfo("success", [{
            "model": "Nikon D90"
        }, {
            "model": "Nikon D90"
        }])
        
    def test_serialNumbers(self):
        cams = cameras.MockCameras(self.resources, 
                                   "${testData}/supported-cameras-test-data.json")
        serialNumbers = cams.serialNumbers()
        self.assertEquals(2, len(serialNumbers))
        self.assertEquals("abc", serialNumbers[0])
        self.assertEquals("xyz", serialNumbers[1])
        