import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import conventional
from store import FSStore
from utils import io

CONVENTIONAL_DIR = os.path.abspath(os.path.join("data", "conventional"))
CAPTURE_STATUS_FILENAME = "captureStatus.json"

class TestConventional(unittest.TestCase):
    
    conventional = None
    
    def setUp(self):
        self.statusFile = os.path.join(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME)
        self.conventional = conventional.Conventional(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, True)
    
    def tearDown(self):
        io.rmTree(CONVENTIONAL_DIR)
        
    def test_01_init(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))

    def test_02_capture(self):
        expected = [os.path.abspath(os.path.join(CONVENTIONAL_DIR, "capture-0_0.jpg")), os.path.abspath(os.path.join(CONVENTIONAL_DIR, "capture-0_1.jpg"))]
        
        self.assertListEqual(self.conventional.capture(), expected)
        self.assertTrue(os.path.exists(self.statusFile))
        
        fsstore = FSStore(self.statusFile)
        status = fsstore.load()
        self.assertEqual(status["index"], 1)
        self.assertEqual(status["totalCaptures"], 2)
        
    def test_03_delete(self):
        self.conventional.delete()
        self.assertFalse(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should have been removed".format(CONVENTIONAL_DIR))
        
    def test_04_getImagesByIndex(self):
        imgDir = os.path.join("mockData", "images")
        img1 = os.path.join(imgDir, "capture-0_1.jpg")
        img2 = os.path.join(imgDir, "capture-0_2.jpg")
        t1 = self.conventional.getImagesByIndex("1", imgDir)
        t2 = self.conventional.getImagesByIndex("0", imgDir, filenameTemplate="capture-${captureIndex}_${cameraID}")
        self.assertListEqual([img1], t1)
        self.assertListEqual([img1, img2], t2)
        
if __name__ == '__main__':
    unittest.main()