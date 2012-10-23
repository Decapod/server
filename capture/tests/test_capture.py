import sys
import os
import shutil
import zipfile
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import capture
import cameraInterface
from store import FSStore
from status import Status
import utils

DATA_DIR = os.path.abspath("data")
MOCK_DATA_DIR = os.path.abspath("mockData")
CONVENTIONAL_DIR = os.path.join(DATA_DIR, "conventional")
CONVENTIONAL_CAPTURES_DIR = os.path.join(CONVENTIONAL_DIR, "captures")
CAPTURE_STATUS_FILENAME = "captureStatus.json"
MOCK_CONFIG = {"testmode": True, "multiCapture": "simultaneousCapture", "delay": 10, "interval": 1}

class TestCapture(unittest.TestCase):
    
    capture = None
    
    def setUp(self):
        self.statusFile = os.path.join(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME)
        self.capture = capture.Capture(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, MOCK_CONFIG)
    
    def tearDown(self):
        utils.io.rmTree(CONVENTIONAL_DIR)
        capture.Capture.trackedCameraPorts = None
        
    def test_01_init(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))

    def test_02_getCamerasStatus(self):
        eCode = "READY"
        expected = {"statusCode": eCode, "message": cameraInterface.CAMERA_STATUS[eCode]}
        self.assertDictEqual(self.capture.getCamerasStatus(), expected)

        capture.Capture.trackedCameraPorts = ["usb:001,002"]
        eCode = "READY"
        expected = {"statusCode": eCode, "message": cameraInterface.CAMERA_STATUS[eCode]}
        self.assertDictEqual(self.capture.getCamerasStatus(), expected)
        
        capture.Capture.trackedCameraPorts = ["usb:001,002", "usb:001,003", "usb:001,004"]
        eCode = "CAMERA_DISCONNECTED"
        expected = {"statusCode": eCode, "message": cameraInterface.CAMERA_STATUS[eCode], "numCamerasDisconnected": 1}
        self.assertDictEqual(self.capture.getCamerasStatus(), expected)
    
    def test_03_updateCaptureIndices(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)

        shutil.copy(images[0], os.path.join(captureDir, "capture-1_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-2_0.jpg"))
        
        self.capture.updateCaptureIndices()
        self.assertEquals(self.capture.status.model["firstCaptureIndex"], 1)
        self.assertEquals(self.capture.status.model["lastCaptureIndex"], 2)
        
    def test_04_updateCaptureIndices_noImages(self):
        self.capture.status.model["firstCaptureIndex"] = 2
        self.capture.status.model["lastCaptureIndex"] = 10
        
        self.capture.updateCaptureIndices()
        self.assertEquals(self.capture.status.model["firstCaptureIndex"], 0)
        self.assertEquals(self.capture.status.model["lastCaptureIndex"], 0)
    
    def test_05_capture(self):
        expected = ({"index": 1, "firstCaptureIndex": 1, "lastCaptureIndex": 1, "totalCaptures": 1}, [os.path.abspath(os.path.join(CONVENTIONAL_CAPTURES_DIR, "capture-1_0.jpeg")), os.path.abspath(os.path.join(CONVENTIONAL_CAPTURES_DIR, "capture-1_1.jpeg"))])
        
        captureResult = self.capture.capture()
        self.assertDictEqual(expected[0], captureResult[0])
        self.assertEqual(expected[1], captureResult[1])
        self.assertTrue(os.path.exists(self.statusFile))
        
        status = self.capture.status.model
        self.assertEqual(status["index"], 1)
        self.assertEqual(status["totalCaptures"], 1)
        
    def test_06_multiCapture_fallback(self):
        capture.Capture.trackedMultiCaptureFunc = None  # reset trackedMultiCaptureFunc for the new config
        config = {"testmode": True, "multiCapture": "raiseTimeoutError", "delay": 10, "interval": 1}
        captureObj = capture.Capture(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, config)
        
        expected = "sequentialCapture"
        
        captureObj.capture()
        self.assertEqual(captureObj.trackedMultiCaptureFunc, expected)
        
        status = captureObj.status.model
        self.assertEqual(status["index"], 1)
        self.assertEqual(status["totalCaptures"], 1)

    def test_07_delete(self):
        self.capture.delete()
        self.assertDictEqual({"index": 0, "firstCaptureIndex": 0, "lastCaptureIndex": 0, "totalCaptures": 0}, self.capture.status.model)
        self.assertListEqual(["captureStatus.json"], os.listdir(CONVENTIONAL_DIR))
    
    def test_08_getImagesByIndex(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        for image in images:
            shutil.copy(image, captureDir)
            
        img1 = os.path.join(captureDir, "capture-0_1.jpg")
        img2 = os.path.join(captureDir, "capture-0_2.jpg")
        t1 = self.capture.getImagesByIndex("1", filenameTemplate="capture-${cameraID}_${index}")
        t2 = self.capture.getImagesByIndex("0")
        self.assertListEqual([img1], t1)
        self.assertListEqual([img2, img1], t2)
        
    def test_09_deleteImagesByIndex_last(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)

        shutil.copy(images[0], os.path.join(captureDir, "capture-1_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-1_1.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-2_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-2_1.jpg"))

        self.capture.status.update("index", 2)
        self.capture.status.update("totalCaptures", 2)
        self.capture.status.update("lastCaptureIndex", 2)
        self.capture.status.update("firstCaptureIndex", 1)
        
        self.capture.deleteImagesByIndex("2")
        self.assertListEqual([], self.capture.getImagesByIndex("2"))
        self.assertDictEqual({"index": 2, "firstCaptureIndex": 1, "lastCaptureIndex": 1, "totalCaptures": 1}, self.capture.status.model)
        
    def test_10_deleteImagesByIndex_first(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)

        shutil.copy(images[0], os.path.join(captureDir, "capture-1_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-1_1.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-2_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-2_1.jpg"))

        self.capture.status.update("index", 2)
        self.capture.status.update("totalCaptures", 2)
        self.capture.status.update("lastCaptureIndex", 2)
        self.capture.status.update("firstCaptureIndex", 1)
        
        self.capture.deleteImagesByIndex("1")
        self.assertListEqual([], self.capture.getImagesByIndex("1"))
        self.assertDictEqual({"index": 2, "firstCaptureIndex": 2, "lastCaptureIndex": 2, "totalCaptures": 1}, self.capture.status.model)
        
    def test_11_deleteImagesByIndex_all(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)

        shutil.copy(images[0], os.path.join(captureDir, "capture-1_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-1_1.jpg"))

        self.capture.status.update("index", 1)
        self.capture.status.update("totalCaptures", 1)
        self.capture.status.update("lastCaptureIndex", 1)
        self.capture.status.update("firstCaptureIndex", 1)
        
        self.capture.deleteImagesByIndex("1")
        self.assertListEqual([], self.capture.getImagesByIndex("1"))
        self.assertDictEqual({"index": 1, "firstCaptureIndex": 0, "lastCaptureIndex": 0, "totalCaptures": 0}, self.capture.status.model)
        
    def test_12_deleteImages(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        for image in images:
            shutil.copy(image, captureDir)
        self.capture.status.update("totalCaptures", len(images))
        
        self.capture.deleteImages()
        self.assertListEqual([], utils.image.findImages(captureDir))
        self.assertDictEqual({"index": 0, "firstCaptureIndex": 0, "lastCaptureIndex": 0, "totalCaptures": 0}, self.capture.status.model)
        
    def test_13_indices(self):
        expected = (19, 1)
        results = self.capture.indices("capture-{0}_{1}.jpeg".format(expected[0], expected[1]));
        self.assertTupleEqual(expected, results)
        
    def test_14_sort(self):
        expectedFiles = [os.path.join(self.capture.captureDir, "capture-0_1.jpg"), os.path.join(self.capture.captureDir, "capture-0_2.jpg")]
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        
        for image in images:
            shutil.copy(image, captureDir)
        
        self.assertListEqual(expectedFiles, self.capture.sort())
        
    def test_15_sort_reversed(self):
        expectedFiles = [os.path.join(self.capture.captureDir, "capture-0_2.jpg"), os.path.join(self.capture.captureDir, "capture-0_1.jpg")]
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        
        for image in images:
            shutil.copy(image, captureDir)
        
        self.assertListEqual(expectedFiles, self.capture.sort(reverse=True))
        
    def test_16_sort_nonContinuous(self):
        captureFiles = ["capture-0_1.jpg", "capture-1_1.jpg", "capture-1_2.jpg", "capture-3_1.jpg", "capture-10_1.jpg"]
        expectedFiles = map(lambda fileName: os.path.join(self.capture.captureDir, fileName), captureFiles)
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        
        for path in expectedFiles:
            shutil.copy(images[0], path)
        
        self.assertListEqual(expectedFiles, self.capture.sort())
        
    def test_17_export(self):
        expectedFiles = ["capture-0_1.jpg", "capture-0_2.jpg"]
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)
        
        for image in images:
            shutil.copy(image, captureDir)
        
        zipPath = self.capture.export()
        self.assertTrue(os.path.exists(zipPath))
        self.assertTrue(zipfile.is_zipfile(zipPath))
        
        zip = zipfile.ZipFile(zipPath, "r")
        self.assertIsNone(zip.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zip.namelist())
        zip.close()

    def test_18_export_nonContinuousCaptures(self):
        expectedFiles = ["capture-0_0.jpg", "capture-0_1.jpg", "capture-1_0.jpg", "capture-1_1.jpg"]
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        captureDir = self.capture.captureDir
        images = utils.image.findImages(imgDir)

        shutil.copy(images[0], os.path.join(captureDir, "capture-0_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-0_1.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-3_0.jpg"))
        shutil.copy(images[0], os.path.join(captureDir, "capture-3_1.jpg"))
        
        zipPath = self.capture.export()
        self.assertTrue(os.path.exists(zipPath))
        self.assertTrue(zipfile.is_zipfile(zipPath))
        
        zip = zipfile.ZipFile(zipPath, "r")
        self.assertIsNone(zip.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zip.namelist())
        zip.close()        

if __name__ == '__main__':
    unittest.main()