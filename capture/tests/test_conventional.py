import sys
import os
import shutil
import zipfile
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import conventional
from store import FSStore
from status import Status
import utils

DATA_DIR = os.path.abspath("data")
MOCK_DATA_DIR = os.path.abspath("mockData")
CONVENTIONAL_DIR = os.path.join(DATA_DIR, "conventional")
CONVENTIONAL_CAPTURES_DIR = os.path.join(CONVENTIONAL_DIR, "captures")
CAPTURE_STATUS_FILENAME = "captureStatus.json"
MOCK_CONFIG = {"testmode": True, "multiCapture": "simultaneousCapture", "delay": 10, "interval": 1}

class TestConventional(unittest.TestCase):
    
    conventional = None
    
    def setUp(self):
        self.statusFile = os.path.join(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME)
        self.conventional = conventional.Conventional(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, MOCK_CONFIG)
    
    def tearDown(self):
        utils.io.rmTree(CONVENTIONAL_DIR)
        
    def test_01_init(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))

    def test_02_capture(self):
        expected = [os.path.abspath(os.path.join(CONVENTIONAL_CAPTURES_DIR, "capture-0_0.jpeg")), os.path.abspath(os.path.join(CONVENTIONAL_CAPTURES_DIR, "capture-0_1.jpeg"))]
        
        self.assertListEqual(self.conventional.capture(), expected)
        self.assertTrue(os.path.exists(self.statusFile))
        
        status = self.conventional.status.model
        self.assertEqual(status["index"], 1)
        self.assertEqual(status["totalCaptures"], 2)
        
    def test_03_multiCapture_fallback(self):
        conventional.Conventional.trackedMultiCaptureFunc = None  # reset trackedMultiCaptureFunc for the new config
        config = {"testmode": True, "multiCapture": "raiseTimeoutError", "delay": 10, "interval": 1}
        conventionalObj = conventional.Conventional(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, config)
        
        expected = "sequentialCapture"
        
        conventionalObj.capture()
        self.assertEqual(conventionalObj.trackedMultiCaptureFunc, expected)
        
        status = conventionalObj.status.model
        self.assertEqual(status["index"], 1)
        self.assertEqual(status["totalCaptures"], 2)

    def test_04_delete(self):
        self.conventional.delete()
        self.assertFalse(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should have been removed".format(CONVENTIONAL_DIR))
        
    def test_05_getImagesByIndex(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.conventional.captureDir
        images = utils.image.findImages(imgDir)
        for image in images:
            shutil.copy(image, captureDir)
            
        img1 = os.path.join(captureDir, "capture-0_1.jpg")
        img2 = os.path.join(captureDir, "capture-0_2.jpg")
        t1 = self.conventional.getImagesByIndex("1", filenameTemplate="capture-${cameraID}_${captureIndex}")
        t2 = self.conventional.getImagesByIndex("0")
        self.assertListEqual([img1], t1)
        self.assertListEqual([img2, img1], t2)
        
    def test_06_deleteImagesByIndex(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.conventional.captureDir
        images = utils.image.findImages(imgDir)
        for image in images:
            shutil.copy(image, captureDir)
        self.conventional.status.update("totalCaptures", len(images))
        
        self.conventional.deleteImagesByIndex("1", filenameTemplate="capture-${cameraID}_${captureIndex}")
        self.assertListEqual([], self.conventional.getImagesByIndex("1"))
        self.assertEquals(1, self.conventional.status.model["totalCaptures"])
        
    def test_05_export(self):
        expectedFiles = ["capture-0_2.jpg", "capture-0_1.jpg"]
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.conventional.captureDir
        images = utils.image.findImages(imgDir)
        
        for image in images:
            shutil.copy(image, captureDir)
        
        zipPath = self.conventional.export()
        self.assertTrue(os.path.exists(zipPath))
        self.assertTrue(zipfile.is_zipfile(zipPath))
        
        zip = zipfile.ZipFile(zipPath, "r")
        self.assertIsNone(zip.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zip.namelist())
        zip.close()
        
if __name__ == '__main__':
    unittest.main()