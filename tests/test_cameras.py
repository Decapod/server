import sys
import os
import unittest
import testutils

sys.path.append(os.path.abspath('..'))
import cameras

class CamerasTest(unittest.TestCase):

    cameras = None
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
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()

    def tearDown(self):
        testutils.cleanUpCapturedImages()
        
    def checkCameraInfo(self, expectedStatus, connectedCameras):
        self.cameras = cameras.MockCameras(self.resources, 
                                           "${testData}/supported-cameras-test-data.json", 
                                           connectedCameras)
        status = self.cameras.status()
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