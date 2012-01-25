import sys
import os
import unittest
import filecmp

import testutils
sys.path.append(os.path.abspath('..'))
import imageImport

class ImportImageTest(unittest.TestCase):

    resources = None
    testDataDir = None
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()
        self.testDataDir = self.resources.filePath("${testData}")
        
    def tearDown(self):
        testutils.cleanUpImages()
    
    # Custom assertions
    def assertNameFormat(self, name, prefix="decapod-", suffix="jpeg"):
        self.assertTrue(name.startswith(prefix), "Tests if '{0}' starts with {1}".format(name, prefix))
        self.assertTrue(name.endswith(suffix), "Tests if '{0}' ends with {1}".format(name, suffix))
        
    def assertFileWritten(self, origFilePath, writePath):
        self.assertTrue(os.path.exists(writePath), "Tests the existence of the file: {0}".format(writePath))
        self.assertTrue(filecmp.cmp(origFilePath, writePath), "Tests if two files are equivalent\noriginal: {0}\nnew: {1}".format(origFilePath, writePath))
    
    # Convenience test functions   
    def mimeToSuffixTest(self, mimetype, expectedSuffix):
        iImport = imageImport.ImageImport(self.resources)
        
        suffix = iImport.mimeToSuffix(mimetype)
        self.assertEquals(expectedSuffix, suffix)
        
    def saveTest(self, name=None):
        iImport = imageImport.ImageImport(self.resources)
        origFilePath = os.path.join(self.testDataDir, "images/cactus.jpg")
        testFile = testutils.mockFileStream(origFilePath)
        
        savedfile = iImport.save(testFile, name)
        self.assertFileWritten(origFilePath, savedfile)
    
    # Tests
    def test_01_generateImageName_default(self):
        iImport = imageImport.ImageImport(self.resources)
        name = iImport.generateImageName()
        self.assertNameFormat(name)
        
    def test_02_generateImageName_prefix(self):
        iImport = imageImport.ImageImport(self.resources)
        prefix = "decaTest-"
        name = iImport.generateImageName(prefix)
        self.assertNameFormat(name, prefix)
        
    def test_03_generateImageName_suffix(self):
        iImport = imageImport.ImageImport(self.resources)
        suffix = "png"
        name = iImport.generateImageName(suffix=suffix)
        self.assertNameFormat(name, suffix=suffix)
        
    def test_04_generateImageName_custom(self):
        iImport = imageImport.ImageImport(self.resources)
        prefix = "decaTest-"
        suffix = "png"
        name = iImport.generateImageName(prefix, suffix)
        self.assertNameFormat(name, prefix, suffix)
        
    def test_05_generateImageName_UUID(self):
        iImport = imageImport.ImageImport(self.resources)
        numNames = 10
        names = []
        uuidList = None
        
        for i in range(numNames):
            names.append(iImport.generateImageName())
        uuidList = map(None, names)
        
        self.assertEquals(len(names), numNames, "The names list should be populated with {0} different names".format(numNames))
        self.assertEquals(len(uuidList),  numNames, "All the generated names should be unique")
    
    def test_06_mimeToSuffix_mimetype(self):
        self.mimeToSuffixTest("image/png", "png")
    
    def test_07_mimeToSuffix_type(self):
        self.mimeToSuffixTest("png", "png")
        
    def test_08_getFileType(self):
        iImport = imageImport.ImageImport(self.resources)
        origFilePath = os.path.join(self.testDataDir, "images/cactus.jpg")
        testFile = testutils.mockFileStream(origFilePath)
        expectedType = "jpeg"
        
        type = iImport.getFileType(testFile)
        self.assertEquals(expectedType, type)
        
    def test_09_writeFile(self):
        iImport = imageImport.ImageImport(self.resources)
        writePath = os.path.join(iImport.importDir, "cactus.jpg")
        origFilePath = os.path.join(self.testDataDir, "images/cactus.jpg")
        testFile = testutils.mockFileStream(origFilePath)
        
        iImport.writeFile(testFile, writePath)
        self.assertFileWritten(origFilePath, writePath)
        
    def test_10_save_default(self):
        self.saveTest()
        
    def test_11_save_name(self):
        self.saveTest("testName.jpeg")
