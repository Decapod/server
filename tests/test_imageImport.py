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
    
    def extractUUID(self, name):
        return name.split("-")[1]
        
    def test_generateImageName(self):
        '''
        Tests the generateImageName function. There are 4 tests run.
        1) Tests the default output
        2) Tests the output when a prefix is passed in
        3) Tests the output when a suffix is passed in
        4) Tests the output when both the prefix and suffix are specified
        '''
        iImport = imageImport.ImageImport(self.resources)
        dPrefix = "decapod-"
        dSuffix = "jpeg"
        cPrefix = "decaTest-"
        cSuffix = "png"
        
        defaultName = iImport.generateImageName()
        dnName, dnExt = os.path.splitext(defaultName)
        
        customPrefix = iImport.generateImageName(cPrefix)
        cpName, cpExt = os.path.splitext(customPrefix)
        
        customSuffix = iImport.generateImageName(suffix=cSuffix)
        csName, csExt = os.path.splitext(customSuffix)
        
        customArgs = iImport.generateImageName(cPrefix, cSuffix)
        caName, caExt = os.path.splitext(customArgs)
        
        #Assert that the prefixes are set correctly for each generated name
        self.assertTrue(dnName.startswith(dPrefix), "Tests if '{}' starts with {}".format(dnName, dPrefix))
        self.assertTrue(cpName.startswith(cPrefix), "Tests if '{}' starts with {}".format(cpName, cPrefix))
        self.assertTrue(csName.startswith(dPrefix), "Tests if '{}' starts with {}".format(csName, dPrefix))
        self.assertTrue(caName.startswith(cPrefix), "Tests if '{}' starts with {}".format(caName, cPrefix))
        
        #Assert that the suffixes are set correctly for each generated name
        self.assertTrue(dnExt.endswith(dSuffix), "Tests if '{}' ends with {}".format(dnExt, dSuffix))
        self.assertTrue(cpExt.endswith(dSuffix), "Tests if '{}' ends with {}".format(cpExt, dSuffix))
        self.assertTrue(csExt.endswith(cSuffix), "Tests if '{}' ends with {}".format(csExt, cSuffix))
        self.assertTrue(caExt.endswith(cSuffix), "Tests if '{}' ends with {}".format(caExt, cSuffix))
        
        #Assert that the uuid's are different
        uuidList = map(self.extractUUID, [dnName, cpName, csName, caName])
        
        # Uses the set method to remove duplicate values. If there are duplicate
        # UUIDs, the lengths will be different and the assertion will fail
        self.assertEquals(len(uuidList), len(set(uuidList)), "Test if there are duplicate UUIDs")
        
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
        origFilePath = self.testDataDir + "/images/cactus.jpg"
        testFile = testutils.mockFileStream(origFilePath)
        
        savedfile = iImport.save(testFile)
        self.writeTest(origFilePath, savedfile)
        
        savedNamedFile = iImport.save(testFile, name)
        self.writeTest(origFilePath, savedNamedFile)

        