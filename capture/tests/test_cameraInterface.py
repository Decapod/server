import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import cameraInterface

class TestCameraStatus(unittest.TestCase):
    '''
    Only contain the tests for generating the camera status dict.
    Most camera interface functionalities are not testable without connected cameras.
    '''
        
    def test_01_generateCameraStatus(self):
        eCode = "NO_CAMERAS"
        expected = {"statusCode": eCode, "message": cameraInterface.CAMERA_STATUS[eCode]}
        self.assertDictEqual(expected, cameraInterface.generateCameraStatus(eCode))

    def test_02_generateCameraStatus_kwargs(self):
        eCode = "NO_CAPTURE"
        expected = {"statusCode": eCode, "message": cameraInterface.CAMERA_STATUS[eCode], "cameras": ["Camera Model"]}
        self.assertDictEqual(expected, cameraInterface.generateCameraStatus(eCode, cameras=["Camera Model"]))
        
if __name__ == '__main__':
    unittest.main()