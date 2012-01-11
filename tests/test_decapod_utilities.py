import sys
import os
import unittest
import shutil
import glob
sys.path.append(os.path.abspath('..'))
import decapod_utilities as utils

class ResourceSourceTest(unittest.TestCase):
    
    testDir = "test_decapod_utilities_temp_dir"

    def tearDown(self):
        if os.path.exists(self.testDir):
            shutil.rmtree(self.testDir)
            
    def checkForDir(self, path, originalNumFiles):           
        self.assertTrue(os.path.exists(self.testDir),
                        "The test directory should be there.")
        self.assertTrue(os.path.isdir(self.testDir),
                        "The path created should actually be a directory.")
        numFiles = len(glob.glob("*"))
        self.assertEquals(numFiles, originalNumFiles + 1,
                          "There should be only one new change in the current directory.")
            
    def test_mkdirIfNecessary(self):
        # Sanity check first.
        self.assertFalse(os.path.exists(self.testDir),
                         "test_mkdirIfNecessary needs a clean environment, \
                         but the test dir already exists")
        originalNumFiles = len(glob.glob("*"))

         # Try making a new directory.
        utils.mkdirIfNecessary(self.testDir)
        self.checkForDir(self.testDir, originalNumFiles)

        # Try again. Nothing special should happen.
        utils.mkdirIfNecessary(self.testDir)
        self.checkForDir(self.testDir, originalNumFiles)

        # Now delete and try again.
        shutil.rmtree(self.testDir)
        utils.mkdirIfNecessary(self.testDir)
        self.checkForDir(self.testDir, originalNumFiles)
                        
    def test_invokeCommandSync(self):
        # Test a basic command line program
        expectedOutput = "Hello Test!"
        cmd = ["echo", expectedOutput]
        output = utils.invokeCommandSync(cmd,
                                         Exception,
                                         "An error occurred while invoking a command line program")
        self.assertEquals(expectedOutput + "\n", output)
        
        # Now test a program that doesn't exist.
        cmd = ["this_command_doesnt_exist", "--foo"]
        try:
            output = utils.invokeCommandSync(cmd,
                                             Exception,
                                             "invokeCommand correctly throws an exception")
            self.fail("Invoking an invalid command should not succeed.")
        except Exception:
            self.assertTrue(True,
                            "An exception should be thrown when trying to invoke an invalid command.")