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
        testutils.cleanUpCapturedImages()
        
    def test_generateImageName(self):
        '''
        Tests the generateImageName function. There are 4 tests run.
        1) Tests the default output
        2) Tests the output when a prefix is passed in
        3) Tests the output when a suffix is passed in
        4) Tests the output when both the prefix and suffix are specified
        '''
        iImport = imageImport.ImageImport(self.resources)
        prefix = "decaTest-"
        suffix = "png"
        
        defaultName = iImport.generateImageName()
        customPrefix = iImport.generateImageName(prefix)
        customSuffix = iImport.generateImageName(suffix=suffix)
        customArgs = iImport.generateImageName(prefix, suffix)
        
        self.assertEquals("decapod-1.jpg", defaultName)
        self.assertEquals("decaTest-2.jpg", customPrefix)
        self.assertEquals("decapod-3.png", customSuffix)
        self.assertEquals("decaTest-4.png", customArgs)
        
    def test_mimeToSuffix(self):
        '''
        Tests the mimeToSuffix function.
        Ensures that the extension is returned when a mime type is passed in.
        Also tests that if an extension is passed in, it is just returned as is.
        '''
        
        iImport = imageImport.ImageImport(self.resources)
        expectedType = "png"
        
        mime = iImport.mimeToSuffix("image/png")
        type = iImport.mimeToSuffix("png")
        
        self.assertEquals(expectedType, mime)
        self.assertEquals(expectedType, type)
        
    def writeTest(self, origFilePath, writePath):
        '''
        Convenience function to test that a file is read in and written to disk.
        This is done by testing that the new file exists and that the new and 
        original files are the same.
        '''
        
        self.assertTrue(os.path.exists(writePath), "Tests the existence of the file: {}".format(writePath))
        self.assertTrue(filecmp.cmp(origFilePath, writePath), "Tests if two files are equivalent\noriginal: {}\nnew: {}".format(origFilePath, writePath))
        
    def test_writeFile(self):
        '''
        Test the writeFile function.
        Ensures that a file is saved to the file system
        '''
        
        iImport = imageImport.ImageImport(self.resources)
        writePath = iImport.importDir + "cactus.jpg"
        origFilePath = self.testDataDir + "/images/cactus.jpg"
        testFile = testutils.mockFileStream(origFilePath)
        
        iImport.writeFile(testFile, writePath)
        self.writeTest(origFilePath, writePath)
        
    def test_save(self):
        '''
        Test the save function
        Ensures that a files is saved to the file system.
        There are two tests
        1) Tests the default name given to the saved file
        2) Tests when a name for the file is passed in
        '''
        
        iImport = imageImport.ImageImport(self.resources)
        name = "testName.jpeg"
        basePath = iImport.importDir + "{}"
        origFilePath = self.testDataDir + "/images/cactus.jpg"
        testFile = testutils.mockFileStream(origFilePath)
        
        iImport.save(testFile)
        self.writeTest(origFilePath, basePath.format("decapod-1.jpeg"))
        
        iImport.save(testFile, name)
        self.writeTest(origFilePath, basePath.format(name))

        