import sys
import os
import unittest
import shutil
import time
sys.path.append(os.path.abspath('..'))
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
IMG_DIR = os.path.join(DATA_DIR, "images")
TEST_DIR = os.path.join(DATA_DIR, "testDir")

class CommandInvokationTests(unittest.TestCase):
                        
    def test_01_invokeCommandSync_valid(self):
        # Test a basic command line program
        expectedOutput = "Hello Test!"
        cmd = ["echo", expectedOutput]
        output = utils.invokeCommandSync(cmd,
                                         Exception,
                                         "An error occurred while invoking a command line program")
        self.assertEquals(expectedOutput + "\n", output)
        
    def test_02_invokeCommandSync_invalid(self):
        # Test a program that doesn't exist.
        cmd = ["this_command_doesnt_exist", "--foo"]
        self.assertRaises(Exception, utils.invokeCommandSync, cmd, Exception, "inovkeCommand correctly throws an exception")

class DirectoryManipulationTests(unittest.TestCase):
    
    newTestDir = os.path.abspath("new_dir")
    existingTestDir = os.path.abspath("existing_dir")
    
    def setUp(self):
        # Not using the decapod utilites function "makeDirs" because it will be tested here
        if not os.path.exists(self.existingTestDir):
            os.mkdir(self.existingTestDir)
    
    def tearDown(self):
        # Not using the decapod utilites function "rmTree" because it will be tested here
        if os.path.exists(self.newTestDir):
            shutil.rmtree(self.newTestDir)
            
    def assertDirExists(self, path):           
        self.assertTrue(os.path.exists(path), "The test directory should be there.")
        self.assertTrue(os.path.isdir(path), "The path created should actually be a directory.")
        
    def assertNoDir(self, path):
        self.assertFalse(os.path.exists(path), "The test directory should not exist.")
            
    def test_01_makeDirs_create(self):
        utils.makeDirs(self.newTestDir)
        self.assertDirExists(self.newTestDir)
        
    def test_02_makeDirs_existing(self):
        utils.makeDirs(self.existingTestDir)
        self.assertDirExists(self.existingTestDir)
        
    def test_03_rmTree_none(self):
        utils.rmTree(self.newTestDir)
        self.assertNoDir(self.newTestDir)
    
    def test_04_rmTree_existing(self):
        utils.rmTree(self.existingTestDir)
        self.assertNoDir(self.existingTestDir)
        
class WriteTests(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
        
    def tearDown(self):
        utils.rmTree(TEST_DIR)
    
    def test_01_writeToFile(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        content = "Test File"
        self.assertFalse(os.path.exists(filePath), "The file at path ({0}) should not yet exist".format(filePath))
        #tested function
        utils.writeToFile(content, filePath)
        self.assertTrue(os.path.exists(filePath), "The file at path ({0}) should have been created".format(filePath))
        # read in file
        file = open(filePath, "r")
        read = file.read()
        file.close()
        self.assertEquals(content, read)

class ValidationTests(unittest.TestCase):
    
    def test_01_isImage_image(self):
        image = os.path.join(IMG_DIR, "Image_0015.JPEG")
        self.assertTrue(utils.isImage(image), "The file at path ({0}) should be an image".format(image))
        
    def test_02_isImage_other(self):
        file = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertFalse(utils.isImage(file), "The file at path ({0}) should not be an image".format(file))

class ToListTests(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
    
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        
    def test_01_imageDirToList(self):
        imgList = utils.imageDirToList(IMG_DIR)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(IMG_DIR, "Image_0015.JPEG"), os.path.join(IMG_DIR, "Image_0016.JPEG")], imgList)
        
    def test_02_bookPagesToArray_noImages(self):
        pdfDir = os.path.join(DATA_DIR, "pdf")
        imgList = utils.imageDirToList(pdfDir)
        self.assertEquals(0, len(imgList))
        
    def test_03_bookPagesToArray_mixed(self):
        imgOne = os.path.join(IMG_DIR, "Image_0015.JPEG")
        imgTwo = os.path.join(IMG_DIR, "Image_0016.JPEG")
        pdfOne = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        shutil.copy(imgOne, TEST_DIR)
        shutil.copy(imgTwo, TEST_DIR)
        shutil.copy(pdfOne, TEST_DIR)
        imgList = utils.imageDirToList(TEST_DIR)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(TEST_DIR, "Image_0015.JPEG"), os.path.join(TEST_DIR, "Image_0016.JPEG")], imgList)
        
    def test_04_imageDirToList_reversed(self):
        imgList = utils.imageDirToList(IMG_DIR, reverse=True)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(IMG_DIR, "Image_0016.JPEG"), os.path.join(IMG_DIR, "Image_0015.JPEG")], imgList)
        
    def test_05_imageDirToList_customSort(self):
        imgOne = os.path.join(IMG_DIR, "Image_0015.JPEG")
        imgTwo = os.path.join(IMG_DIR, "Image_0016.JPEG")
        shutil.copy(imgOne, TEST_DIR)
        time.sleep(0.1) # wait 0.1 seconds. Needed because copies happen too quickly
        shutil.copy(imgTwo, TEST_DIR)
        imgList = utils.imageDirToList(TEST_DIR)
        self.assertEquals(2, len(imgList))
        timeImgOne = os.path.getmtime(imgList[0])
        timeImgTwo = os.path.getmtime(imgList[1])
        self.assertTrue(timeImgOne < timeImgTwo, "The first page in the array (time: {0}) should have been modified prior to the second (time: {1})".format(timeImgOne, timeImgTwo))
        
class DictTests(unittest.TestCase):
    
    def test_01_rekey(self):
        orig = {"w": 1, "h": 2}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.rekey(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_02_rekey_extraMapKeys(self):
        orig = {"w": 1, "h": 2}
        keyMap = {"w": "-w", "h": "-h", "width": "-w"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.rekey(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_03_rekey_extraDictKeys(self):
        orig = {"w": 1, "h": 2, "dpi": 300}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.rekey(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_04_rekey_extraDictKeys_preserve(self):
        orig = {"w": 1, "h": 2, "dpi": 300}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2, "dpi": 300}
        
        newMap = utils.rekey(orig, keyMap, preserve=True)
        self.assertDictEqual(expected, newMap)
        
    def test_05_dictToFlagList(self):
        orig = {"-w": 1, "-h": 2}
        expected = ["-w", 1, "-h", 2]
        
        flagList = utils.dictToFlagList(orig)
        self.assertListEqual(expected, flagList)
        
    def test_06_dictToFlagList_emptyDict(self):
        orig = {}
        expected = []
        
        flagList = utils.dictToFlagList(orig)
        self.assertListEqual(expected, flagList)

if __name__ == '__main__':
    unittest.main()
