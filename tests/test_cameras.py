import sys
import os
import unittest

sys.path.append(os.path.abspath('..'))
import cameras

class CamerasTest(unittest.TestCase):
    
    supportedCameras = {
        "Canon": [{
            "model": "foo",
            "label": "bar"
        }]
    }

    cameras = None
    
    def setUp(self):
        self.cameras = cameras.Cameras(self.supportedCameras)

    def test_status(self):
        expectedSuccessStatus = {
            "status": "Awesome",
            "supportedCameras": self.supportedCameras
        }
        
        status = self.cameras.status()
        self.assertEquals(status, expectedSuccessStatus)