import sys
import os
import unittest
import shutil
sys.path.append(os.path.abspath('..'))
import decapod_utilities as utils

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
    
    testDir = os.path.abspath("testDir")
    
    def setUp(self):
        utils.makeDirs(self.testDir)
        
    def tearDown(self):
        utils.rmTree(self.testDir)
    
    def test_01_writeToFile(self):
        filePath = os.path.join(self.testDir, "testFile.txt")
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
        
if __name__ == '__main__':
    unittest.main()
