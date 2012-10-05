import sys
import os
import unittest
import filecmp

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import mockClasses
import imageImport
from utils import io

DATA_DIR = os.path.abspath("data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIBRARY_DIR = os.path.join(DATA_DIR, "library")
BOOK_DIR = os.path.join(LIBRARY_DIR, "book")


# "data/library/book/images/"

class ImportImageTest(unittest.TestCase):
    mockRS = mockClasses.mockResourceSource({"/library": {"path": LIBRARY_DIR}})
    iImport = None
    
    def setUp(self):
        self.iImport = imageImport.ImageImport(self.mockRS)
        
    def tearDown(self):
        io.rmTree(BOOK_DIR)
    
    # Custom assertions
    def assertFileWritten(self, origFilePath, writePath):
        self.assertTrue(os.path.exists(writePath), "Tests the existence of the file: {0}".format(writePath))
        self.assertTrue(filecmp.cmp(origFilePath, writePath), "Tests if two files are equivalent\noriginal: {0}\nnew: {1}".format(origFilePath, writePath))
    
    # Convenience test functions   
    def mimeToSuffixTest(self, iImport, mimetype, expectedSuffix):
        suffix = iImport.mimeToSuffix(mimetype)
        self.assertEquals(expectedSuffix, suffix)
        
    def saveTest(self, iImport, name=None):
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = mockClasses.mockFileStream(origFilePath)
        
        savedfile = iImport.save(testFile, name)
        self.assertFileWritten(origFilePath, savedfile)
    
    # Tests
    def test_01_mimeToSuffix_mimetype(self):
        self.mimeToSuffixTest(self.iImport, "image/png", "png")
    
    def test_02_mimeToSuffix_type(self):
        self.mimeToSuffixTest(self.iImport, "png", "png")
        
    def test_03_getFileType(self):
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = mockClasses.mockFileStream(origFilePath)
        expectedType = "jpeg"
        
        type = self.iImport.getFileType(testFile)
        self.assertEquals(expectedType, type)
        
    def test_04_isValidType_valid(self):
        testFile = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        valid = self.iImport.isValidType(testFile)
        self.assertTrue(valid, "The file at path ({0}) should have been a valid file type".format(testFile))
        
    def test_05_isValidType_invalid(self):
        testFile = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        valid = self.iImport.isValidType(testFile)
        self.assertFalse(valid, "The file at path ({0}) should not have been a valid file type".format(testFile))
        
    def test_06_writeFile(self):
        writePath = os.path.join(self.iImport.importDir, "Image_0015.JPEG")
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = mockClasses.mockFileStream(origFilePath)

        self.iImport.writeFile(testFile, writePath)
        self.assertFileWritten(origFilePath, writePath)
        
    def test_07_save_default(self):
        self.saveTest(self.iImport)
        
    def test_08_save_name(self):
        self.saveTest(self.iImport, "testName.jpeg")
        
    def test_09_save_invalid(self):
        testPath = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        testFile = mockClasses.mockFileStream(testPath)
        self.assertRaises(imageImport.ImportTypeError, self.iImport.save, testFile)

if __name__ == '__main__':
    unittest.main()
