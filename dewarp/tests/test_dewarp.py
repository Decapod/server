import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import dewarp
from utils import io

DATA_DIR = os.path.abspath("data/")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

MOCK_DATA_DIR = os.path.abspath("mockData/")

class TestDewarp(unittest.TestCase):

    status_complete = {"status": "complete", "percentage": 100}
    status_inProgress = {"status": "in progress", "percentage": 0}
    status_ready = {"status": "ready"}
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
        self.dewarp = dewarp.Dewarp(DATA_DIR, STATUS_FILE, True)
        
    def tearDown(self):
        io.rmTree(DATA_DIR)
        self.dewarp = None
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        readStatus = io.loadJSONFile(statusFile)
        self.assertDictEqual(status, readStatus)
            
    def test_01_init(self):
        self.assertEquals(DATA_DIR, self.dewarp.dataDir)
        self.assertTrue(os.path.exists(self.dewarp.dataDir))
        
        self.assertEquals(STATUS_FILE, self.dewarp.statusFilePath)
        self.assertEquals(os.path.join(DATA_DIR, "unpacked"), self.dewarp.unpacked)
        self.assertEquals(os.path.join(DATA_DIR, "dewarped"), self.dewarp.dewarped)
        self.assertEquals(os.path.join(DATA_DIR, "export.zip"), self.dewarp.export)
        
        self.assertDictEqual(self.status_ready, self.dewarp.status.model)
            
    def test_02_init_statusFile(self):
        io.writeToJSONFile(self.status_inProgress, STATUS_FILE)
        self.dewarp = dewarp.Dewarp(DATA_DIR, STATUS_FILE)
        self.assertDictEqual(self.status_inProgress, self.dewarp.status.model)
        self.assertStatusFile(self.status_inProgress, self.dewarp.statusFilePath)
        
    def test_03_getStatus(self):
        status = self.dewarp.getStatus()
        self.assertDictEqual(status, self.dewarp.status.model)
        self.assertDictEqual(status, self.status_ready)
        
    def test_04_isInState(self):
        states = ["complete", "in progress", "ready"]
        for state in states:
            self.dewarp.status.update("status", state)
            self.assertTrue(self.dewarp.isInState(state))
    
    def test_05_isInState_false(self):
        self.assertFalse(self.dewarp.isInState("test"))
    
    def test_06_delete(self):
        self.dewarp.status.update("status", "complete")
        self.dewarp.delete()
        self.assertTrue(os.path.exists(self.dewarp.dataDir))
        self.assertTrue(os.path.exists(self.dewarp.statusFilePath))
        self.assertFalse(os.path.exists(self.dewarp.unpacked))
        self.assertFalse(os.path.exists(self.dewarp.dewarped))
        self.assertFalse(os.path.exists(self.dewarp.export))
        self.assertDictEqual(self.status_ready, self.dewarp.status.model)
        self.assertStatusFile(self.status_ready, self.dewarp.statusFilePath)
    
    def test_07_delete_inProgress(self):
        self.dewarp.status.update("status", "in progress")
        self.assertRaises(dewarp.DewarpInProgressError, self.dewarp.delete)
    
    def test_08_findPairs(self):
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-1_1.jpg"))
        
        matched, unmatched = self.dewarp.findPairs(DATA_DIR)
        self.assertEqual(matched, [(os.path.join(DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))])
        self.assertEqual(unmatched, [os.path.join(DATA_DIR, "capture-1_1.jpg")])

    def test_09_processDewarp_exceptions(self):
        # Test un-existed source directory
        self.assertRaises(dewarp.UnpackedDirNotExistError, self.dewarp.processDewarp, "a", "b")
        
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-1_1.jpg"))
        
        self.assertRaises(dewarp.UnmatchedPairsError, self.dewarp.processDewarp, DATA_DIR, "b")
        
    def test_10_processDewarp_hasPairs(self):
        # Test un-existed source directory
        self.assertRaises(dewarp.UnpackedDirNotExistError, self.dewarp.processDewarp, "a", "b")
        
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        dewarpedDir = os.path.join(DATA_DIR, "dewarped")
        
        io.makeDirs(unpackedDir)
        
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(unpackedDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(unpackedDir, "capture-0_2.jpg"))
        
        self.assertRaises(dewarp.CalibrationDirNotExistError, self.dewarp.processDewarp, unpackedDir, "b")
        
        calibrationDir = os.path.join(unpackedDir, "calibration")
        io.makeDirs(calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(calibrationDir, "calibration.xml"))
#        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration"), unpackedDir)
        
        self.assertTrue(self.dewarp.processDewarp(unpackedDir, dewarpedDir))
        self.assertTrue(os.path.exists(dewarpedDir))

if __name__ == '__main__':
    unittest.main()
