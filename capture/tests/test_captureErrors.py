import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
import captureErrors

class TestCaptureErrors(unittest.TestCase):
        
    def test_01_generateErrorInfo(self):
        eCode = "NO_CAMERAS"
        expected = {"errorCode": eCode, "message": captureErrors.ERROR_CODES[eCode]}
        self.assertDictEqual(expected, captureErrors.generateErrorInfo(eCode))

    def test_02_generateErrorInfo_kwargs(self):
        eCode = "NO_CAPTURE"
        expected = {"errorCode": eCode, "message": captureErrors.ERROR_CODES[eCode], "cameras": ["Camera Model"]}
        self.assertDictEqual(expected, captureErrors.generateErrorInfo(eCode, cameras=["Camera Model"]))
        
if __name__ == '__main__':
    unittest.main()