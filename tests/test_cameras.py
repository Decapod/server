import sys
import os
import unittest
import testutils

sys.path.append(os.path.abspath('..'))
import cameras

class CamerasTest(unittest.TestCase):

    cameras = None
    
    def setUp(self):
        resources = testutils.createTestResourceSource()
        self.cameras = cameras.Cameras(resources, "${testData}/supported-cameras-test-data.json")

    def tearDown(self):
        testutils.cleanUpCapturedImages()
        
    def test_status(self):
        expectedSuccessStatus = {
            "status": "Awesome",
            "supportedCameras": {
                "Canon": [{
                    "model": "foo",
                    "label": "bar"
                }]
            }
        }
        
        status = self.cameras.status()
        self.assertEquals(status, expectedSuccessStatus)