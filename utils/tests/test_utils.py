import sys
import os
import unittest
import shutil
import time
import simplejson as json

import test_utils_helper
sys.path.append(os.path.abspath('..'))
import utils

DATA_DIR = os.path.abspath("data/")
IMG_DIR = os.path.join(DATA_DIR, "images")
FILES_DIR = os.path.join(DATA_DIR, "files")
TEST_DIR = os.path.join(DATA_DIR, "testDir")

class CommandInvokationTests(unittest.TestCase):
                        
    def test_01_invokeCommandSync_valid(self):
        # Test a basic command line program
        expectedOutput = "Hello Test!"
        cmd = ["echo", expectedOutput]
        output = utils.io.invokeCommandSync(cmd,
                                         Exception,
                                         "An error occurred while invoking a command line program")
        self.assertEquals(expectedOutput + "\n", output)
        
    def test_02_invokeCommandSync_invalid(self):
        # Test a program that doesn't exist.
        cmd = ["this_command_doesnt_exist", "--foo"]
        self.assertRaises(Exception, utils.io.invokeCommandSync, cmd, Exception, "inovkeCommand correctly throws an exception")

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
        utils.io.makeDirs(self.newTestDir)
        self.assertDirExists(self.newTestDir)
        
    def test_02_makeDirs_existing(self):
        utils.io.makeDirs(self.existingTestDir)
        self.assertDirExists(self.existingTestDir)
        
    def test_03_rmTree_none(self):
        utils.io.rmTree(self.newTestDir)
        self.assertNoDir(self.newTestDir)
    
    def test_04_rmTree_existing(self):
        utils.io.rmTree(self.existingTestDir)
        self.assertNoDir(self.existingTestDir)
        
class FileOperationTests(unittest.TestCase):

    def setUp(self):
        utils.io.makeDirs(TEST_DIR)
        self.filePath = os.path.join(TEST_DIR, "sample.json")
        self.jsonData = {"test": "test"}
        
    def tearDown(self):
        utils.io.rmTree(TEST_DIR)
        
    def test_01_writeToFile(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        content = "Test File"
        self.assertFalse(os.path.exists(filePath), "The file at path ({0}) should not yet exist".format(filePath))
        #tested function
        utils.io.writeToFile(content, filePath)
        self.assertTrue(os.path.exists(filePath), "The file at path ({0}) should have been created".format(filePath))
        # read in file
        file = open(filePath, "r")
        read = file.read()
        file.close()
        self.assertEquals(content, read) 
        
    def test_02_readFromFile(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        f = open(filePath, "w")
        content = "Test File"
        utils.io.writeToFile(content, filePath)
        readContent = utils.io.readFromFile(filePath)
        self.assertEquals(readContent, content)
        
    def test_03_loadJSONFile(self):
        f = open(self.filePath, "w")
        f.write(json.dumps(self.jsonData))
        f.close()
        loadedJSON = utils.io.loadJSONFile(self.filePath)
        self.assertDictEqual(self.jsonData, loadedJSON)
        
    def test_04_writeToJSONFile(self):
        utils.io.writeToJSONFile(self.jsonData, self.filePath)
        self.assertTrue(os.path.exists(self.filePath), "The path ({0}) to the created json file should exist".format(self.filePath))
        f = open(self.filePath)
        loadedJSON = json.load(f)
        f.close()
        
        self.assertDictEqual(self.jsonData, loadedJSON)
        

class ValidationTests(unittest.TestCase):
    
    def test_01_isImage_image(self):
        image = os.path.join(IMG_DIR, "Image_0015.JPEG")
        self.assertTrue(utils.image.isImage(image), "The file at path ({0}) should be an image".format(image))
        
    def test_02_isImage_other(self):
        file = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertFalse(utils.image.isImage(file), "The file at path ({0}) should not be an image".format(file))

class ToListTests(unittest.TestCase):
    
    def setUp(self):
        utils.io.makeDirs(TEST_DIR)
    
    def tearDown(self):
        utils.io.rmTree(TEST_DIR)
        
    def test_01_imageDirToList(self):
        imgList = utils.image.imageListFromDir(IMG_DIR)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(IMG_DIR, "Image_0015.JPEG"), os.path.join(IMG_DIR, "Image_0016.JPEG")], imgList)
        
    def test_02_bookPagesToArray_noImages(self):
        imgList = utils.image.imageListFromDir(FILES_DIR)
        self.assertEquals(0, len(imgList))
        
    def test_03_bookPagesToArray_mixed(self):
        imgOne = os.path.join(IMG_DIR, "Image_0015.JPEG")
        imgTwo = os.path.join(IMG_DIR, "Image_0016.JPEG")
        pdfOne = os.path.join(FILES_DIR, "Decapod.pdf")
        shutil.copy(imgOne, TEST_DIR)
        shutil.copy(imgTwo, TEST_DIR)
        shutil.copy(pdfOne, TEST_DIR)
        imgList = utils.image.imageListFromDir(TEST_DIR)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(TEST_DIR, "Image_0015.JPEG"), os.path.join(TEST_DIR, "Image_0016.JPEG")], imgList)
        
    def test_04_imageDirToList_reversed(self):
        imgList = utils.image.imageListFromDir(IMG_DIR, reverse=True)
        self.assertEquals(2, len(imgList))
        self.assertListEqual([os.path.join(IMG_DIR, "Image_0016.JPEG"), os.path.join(IMG_DIR, "Image_0015.JPEG")], imgList)
        
    def test_05_imageDirToList_customSort(self):
        imgOne = os.path.join(IMG_DIR, "Image_0016.JPEG")
        imgTwo = os.path.join(IMG_DIR, "Image_0015.JPEG")
        shutil.copy(imgOne, TEST_DIR)
        time.sleep(0.1) # wait 0.1 seconds. Needed because copies happen too quickly
        shutil.copy(imgTwo, TEST_DIR)
        imgList = utils.image.imageListFromDir(TEST_DIR, sortKey=os.path.getmtime)
        self.assertEquals(2, len(imgList))
        timeImgOne = os.path.getmtime(imgList[0])
        timeImgTwo = os.path.getmtime(imgList[1])
        self.assertTrue(timeImgOne < timeImgTwo, "The first page in the array (time: {0}) should have been modified prior to the second (time: {1})".format(timeImgOne, timeImgTwo))
        
class DictTests(unittest.TestCase):
    
    def test_01_rekey(self):
        orig = {"w": 1, "h": 2}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.translate.map(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_02_rekey_extraMapKeys(self):
        orig = {"w": 1, "h": 2}
        keyMap = {"w": "-w", "h": "-h", "width": "-w"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.translate.map(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_03_rekey_extraDictKeys(self):
        orig = {"w": 1, "h": 2, "dpi": 300}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2}
        
        newMap = utils.translate.map(orig, keyMap)
        self.assertDictEqual(expected, newMap)
        
    def test_04_rekey_extraDictKeys_preserve(self):
        orig = {"w": 1, "h": 2, "dpi": 300}
        keyMap = {"w": "-w", "h": "-h"}
        expected = {"-w": 1, "-h": 2, "dpi": 300}
        
        newMap = utils.translate.map(orig, keyMap, preserve=True)
        self.assertDictEqual(expected, newMap)
        
    def test_05_dictToFlagList(self):
        orig = {"-w": 1, "-h": 2}
        expected = ["-w", 1, "-h", 2]
        
        flagList = utils.translate.weave(orig)
        self.assertListEqual(expected, flagList)
        
    def test_06_dictToFlagList_emptyDict(self):
        orig = {}
        expected = []
        
        flagList = utils.translate.weave(orig)
        self.assertListEqual(expected, flagList)

class generateImageNameTests(unittest.TestCase):
    
    # Custom assertions
    def assertNameFormat(self, name, prefix="decapod-", suffix="jpeg"):
        self.assertTrue(name.startswith(prefix), "Tests if '{0}' starts with {1}".format(name, prefix))
        self.assertTrue(name.endswith(suffix), "Tests if '{0}' ends with {1}".format(name, suffix))
        
    def test_01_generateImageName_default(self):
        name = utils.image.generateImageName()
        self.assertNameFormat(name)
        
    def test_02_generateImageName_prefix(self):
        prefix = "decaTest-"
        name = utils.image.generateImageName(prefix)
        self.assertNameFormat(name, prefix)
        
    def test_03_generateImageName_suffix(self):
        suffix = "png"
        name = utils.image.generateImageName(suffix=suffix)
        self.assertNameFormat(name, suffix=suffix)
        
    def test_04_generateImageName_custom(self):
        prefix = "decaTest-"
        suffix = "png"
        name = utils.image.generateImageName(prefix, suffix)
        self.assertNameFormat(name, prefix, suffix)
        
    def test_05_generateImageName_UUID(self):
        numNames = 10
        names = []
        uuidList = None
        
        for i in range(numNames):
            names.append(utils.image.generateImageName())
        uuidList = map(None, names)
        
        self.assertEquals(len(names), numNames, "The names list should be populated with {0} different names".format(numNames))
        self.assertEquals(len(uuidList),  numNames, "All the generated names should be unique")

class imageTypeTests(unittest.TestCase):
    
    def setUp(self):
        self.sourceImg = os.path.join(IMG_DIR, "Image_0015.JPEG")
        self.temp = os.path.join(DATA_DIR, "temp")
        utils.io.makeDirs(self.temp)
        
    def tearDown(self):
        utils.io.rmTree(self.temp)

    def test_01_getImageType(self):
        type = utils.image.getImageType(self.sourceImg);
        self.assertEquals("jpeg", type)
        
    def test_02_renameWithExtension_withOrigExtension(self):
        targetImg = os.path.join(self.temp, "testImage.tiff")
        shutil.copyfile(self.sourceImg, targetImg)
        
        expected = os.path.join(self.temp, "testImage.jpeg")
        utils.image.renameWithExtension(targetImg)
        self.assertTrue(os.path.exists(expected))
        
    def test_03_renameWithExtension_withMultiExtension(self):
        targetImg = os.path.join(self.temp, "testImage.a.b.c.tiff")
        shutil.copyfile(self.sourceImg, targetImg)
        
        expected = os.path.join(self.temp, "testImage.a.b.c.jpeg")
        utils.image.renameWithExtension(targetImg)
        self.assertTrue(os.path.exists(expected))
        
    def test_04_renameWithExtension_withoutExtension(self):
        targetImg = os.path.join(self.temp, "testImage")
        shutil.copyfile(self.sourceImg, targetImg)
        
        expected = os.path.join(self.temp, "testImage.jpeg")
        utils.image.renameWithExtension(targetImg)
        self.assertTrue(os.path.exists(expected))

class conversionTests(unittest.TestCase):
    def test_01_convertStrToFunc(self):
        expected = "a test string from a module function"
        func = utils.conversion.convertStrToFunc(test_utils_helper, "returnTestString")
        self.assertEqual(func(), expected)
        
if __name__ == '__main__':
    unittest.main()
