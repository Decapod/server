import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import colourPickerProcessor
from utils import io

MOCK_DATA_DIR = os.path.abspath("mockData/")
COLOUR_FILE = os.path.join("..", "..", "..", "decapod-dewarping", ".colors")

class TestDewarpProcessor(unittest.TestCase):
        
    def tearDown(self):
        io.rmFile(COLOUR_FILE)
        
    def test_01_init(self):
        cpProc = colourPickerProcessor.ColourPickerProcessor(MOCK_DATA_DIR, testmode=True);
        self.assertEquals(MOCK_DATA_DIR, cpProc.imagesDir)
            
    def test_02_pickColours(self):
        cpProc = colourPickerProcessor.ColourPickerProcessor(MOCK_DATA_DIR, testmode=True);
        cpProc.pickColours()
        self.assertTrue(COLOUR_FILE)
            
    def test_03_pickColours_imageDir_not_exist(self):
        cpProc = colourPickerProcessor.ColourPickerProcessor("NOT_EXIST", testmode=True);
        self.assertRaises(colourPickerProcessor.ImagesDirNotExistError, cpProc.pickColours)

if __name__ == '__main__':
    unittest.main()
