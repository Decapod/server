import sys
import os
import unittest
import filecmp

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import testutils
import imageImport
from utils import io

DATA_DIR = os.path.abspath("data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIBRARY_DIR = os.path.join(DATA_DIR, "library")
BOOK_DIR = os.path.join(LIBRARY_DIR, "book")


# "data/library/book/images/"

class ImportImageTest(unittest.TestCase):
    mockRS = testutils.mockResourceSource({"/library": {"path": LIBRARY_DIR}})
    iImport = None
    
    def setUp(self):
        self.iImport = imageImport.ImageImport(self.mockRS)
        
    def tearDown(self):
        io.rmTree(BOOK_DIR)
    
    # Custom assertions
    def assertNameFormat(self, name, prefix="decapod-", suffix="jpeg"):
        self.assertTrue(name.startswith(prefix), "Tests if '{0}' starts with {1}".format(name, prefix))
        self.assertTrue(name.endswith(suffix), "Tests if '{0}' ends with {1}".format(name, suffix))
        
    def assertFileWritten(self, origFilePath, writePath):
        self.assertTrue(os.path.exists(writePath), "Tests the existence of the file: {0}".format(writePath))
        self.assertTrue(filecmp.cmp(origFilePath, writePath), "Tests if two files are equivalent\noriginal: {0}\nnew: {1}".format(origFilePath, writePath))
    
    # Convenience test functions   
    def mimeToSuffixTest(self, iImport, mimetype, expectedSuffix):
        suffix = iImport.mimeToSuffix(mimetype)
        self.assertEquals(expectedSuffix, suffix)
        
    def saveTest(self, iImport, name=None):
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = testutils.mockFileStream(origFilePath)
        
        savedfile = iImport.save(testFile, name)
        self.assertFileWritten(origFilePath, savedfile)
    
    # Tests
    def test_01_generateImageName_default(self):
        name = self.iImport.generateImageName()
        self.assertNameFormat(name)
        
    def test_02_generateImageName_prefix(self):
        prefix = "decaTest-"
        name = self.iImport.generateImageName(prefix)
        self.assertNameFormat(name, prefix)
        
    def test_03_generateImageName_suffix(self):
        suffix = "png"
        name = self.iImport.generateImageName(suffix=suffix)
        self.assertNameFormat(name, suffix=suffix)
        
    def test_04_generateImageName_custom(self):
        prefix = "decaTest-"
        suffix = "png"
        name = self.iImport.generateImageName(prefix, suffix)
        self.assertNameFormat(name, prefix, suffix)
        
    def test_05_generateImageName_UUID(self):
        numNames = 10
        names = []
        uuidList = None
        
        for i in range(numNames):
            names.append(self.iImport.generateImageName())
        uuidList = map(None, names)
        
        self.assertEquals(len(names), numNames, "The names list should be populated with {0} different names".format(numNames))
        self.assertEquals(len(uuidList),  numNames, "All the generated names should be unique")
    
    def test_06_mimeToSuffix_mimetype(self):
        self.mimeToSuffixTest(self.iImport, "image/png", "png")
    
    def test_07_mimeToSuffix_type(self):
        self.mimeToSuffixTest(self.iImport, "png", "png")
        
    def test_08_getFileType(self):
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = testutils.mockFileStream(origFilePath)
        expectedType = "jpeg"
        
        type = self.iImport.getFileType(testFile)
        self.assertEquals(expectedType, type)
        
    def test_09_isValidType_valid(self):
        testFile = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        valid = self.iImport.isValidType(testFile)
        self.assertTrue(valid, "The file at path ({0}) should have been a valid file type".format(testFile))
        
    def test_10_isValidType_invalid(self):
        testFile = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        valid = self.iImport.isValidType(testFile)
        self.assertFalse(valid, "The file at path ({0}) should not have been a valid file type".format(testFile))
        
    def test_11_writeFile(self):
        writePath = os.path.join(self.iImport.importDir, "Image_0015.JPEG")
        origFilePath = os.path.join(IMAGES_DIR, "Image_0015.JPEG")
        testFile = testutils.mockFileStream(origFilePath)

        self.iImport.writeFile(testFile, writePath)
        self.assertFileWritten(origFilePath, writePath)
        
    def test_12_save_default(self):
        self.saveTest(self.iImport)
        
    def test_13_save_name(self):
        self.saveTest(self.iImport, "testName.jpeg")
        
    def test_14_save_invalid(self):
        testPath = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        testFile = testutils.mockFileStream(testPath)
        self.assertRaises(imageImport.ImportTypeError, self.iImport.save, testFile)

if __name__ == '__main__':
    unittest.main()
