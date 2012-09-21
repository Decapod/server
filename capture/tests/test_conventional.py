import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import conventional
#from mockClasses import mockResourceSource
from utils import io

CONVENTIONAL_DIR = os.path.abspath(os.path.join("data", "conventional"))
CAPTURE_STATUS_FILENAME = "captureStatus.json"

class TestConventional(unittest.TestCase):
    
    conventional = None
    
    def setUp(self):
        self.conventional = conventional.Conventional(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, True)
    
    def tearDown(self):
        io.rmTree(CONVENTIONAL_DIR)
        
    def test_01_init(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))

    def test_02_capture(self):
        expected = [os.path.join(CONVENTIONAL_DIR, "capture-0_1.jpg"), os.path.join(CONVENTIONAL_DIR, "capture-0_2.jpg")]
        
        self.assertListEqual(self.conventional.capture(), expected)
        
    def test_03_delete(self):
        self.conventional.delete()
        self.assertFalse(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should have been removed".format(CONVENTIONAL_DIR))

if __name__ == '__main__':
    unittest.main()