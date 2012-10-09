import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import dewarpProcessor
from utils import io

DATA_DIR = os.path.abspath("data/")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

MOCK_DATA_DIR = os.path.abspath("mockData/")

class TestDewarpProcessor(unittest.TestCase):

    status_complete = {"status": "complete", "percentage": 100}
    status_inProgress = {"status": "in progress", "percentage": 0}
    status_ready = {"status": "ready"}
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
        self.dewarpProcessor = dewarpProcessor.DewarpProcessor(DATA_DIR, STATUS_FILE, True)
        
    def tearDown(self):
        io.rmTree(DATA_DIR)
        self.dewarpProcessor = None
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        readStatus = io.loadJSONFile(statusFile)
        self.assertDictEqual(status, readStatus)
            
    def test_01_init(self):
        self.assertEquals(DATA_DIR, self.dewarpProcessor.dataDir)
        self.assertTrue(os.path.exists(self.dewarpProcessor.dataDir))
        
        self.assertEquals(STATUS_FILE, self.dewarpProcessor.statusFilePath)
        self.assertEquals(os.path.join(DATA_DIR, "unpacked"), self.dewarpProcessor.unpacked)
        self.assertEquals(os.path.join(DATA_DIR, "dewarped"), self.dewarpProcessor.dewarped)
        self.assertEquals(os.path.join(DATA_DIR, "export.zip"), self.dewarpProcessor.export)
        
        self.assertDictEqual(self.status_ready, self.dewarpProcessor.status.model)
            
    def test_02_init_statusFile(self):
        io.writeToJSONFile(self.status_inProgress, STATUS_FILE)
        self.dewarpProcessor = dewarpProcessor.DewarpProcessor(DATA_DIR, STATUS_FILE)
        self.assertDictEqual(self.status_inProgress, self.dewarpProcessor.status.model)
        self.assertStatusFile(self.status_inProgress, self.dewarpProcessor.statusFilePath)
        
    def test_03_getStatus(self):
        status = self.dewarpProcessor.getStatus()
        self.assertDictEqual(status, self.dewarpProcessor.status.model)
        self.assertDictEqual(status, self.status_ready)
        
    def test_04_isInState(self):
        states = ["complete", "in progress", "ready"]
        for state in states:
            self.dewarpProcessor.status.update("status", state)
            self.assertTrue(self.dewarpProcessor.isInState(state))
    
    def test_05_isInState_false(self):
        self.assertFalse(self.dewarpProcessor.isInState("test"))
    
    def test_06_delete(self):
        self.dewarpProcessor.status.update("status", "complete")
        self.dewarpProcessor.delete()
        self.assertTrue(os.path.exists(self.dewarpProcessor.dataDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.statusFilePath))
        self.assertFalse(os.path.exists(self.dewarpProcessor.unpacked))
        self.assertFalse(os.path.exists(self.dewarpProcessor.dewarped))
        self.assertFalse(os.path.exists(self.dewarpProcessor.export))
        self.assertDictEqual(self.status_ready, self.dewarpProcessor.status.model)
        self.assertStatusFile(self.status_ready, self.dewarpProcessor.statusFilePath)
    
    def test_07_delete_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.delete)
    
    def test_08_findPairs(self):
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-1_1.jpg"))
        
        matched, unmatched = self.dewarpProcessor.findPairs(DATA_DIR)
        self.assertEqual(matched, [(os.path.join(DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))])
        self.assertEqual(unmatched, [os.path.join(DATA_DIR, "capture-1_1.jpg")])

    def test_09_dewarpImp_exceptions(self):
        # Test un-existed source directory
        self.assertRaises(dewarpProcessor.UnpackedDirNotExistError, self.dewarpProcessor.dewarpImp, "a", "b")
        
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-1_1.jpg"))
        
        self.assertRaises(dewarpProcessor.UnmatchedPairsError, self.dewarpProcessor.dewarpImp, DATA_DIR, "b")
        
    def test_10_dewarpImp_hasPairs(self):
        # Test un-existed source directory
        self.assertRaises(dewarpProcessor.UnpackedDirNotExistError, self.dewarpProcessor.dewarpImp, "a", "b")
        
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        dewarpedDir = os.path.join(DATA_DIR, "dewarped")
        
        io.makeDirs(unpackedDir)
        
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(unpackedDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(unpackedDir, "capture-0_2.jpg"))
        
        self.assertRaises(dewarpProcessor.CalibrationDirNotExistError, self.dewarpProcessor.dewarpImp, unpackedDir, "b")
        
        calibrationDir = os.path.join(unpackedDir, "calibration")
        io.makeDirs(calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(calibrationDir, "calibration.xml"))
        
        self.assertTrue(self.dewarpProcessor.dewarpImp(unpackedDir, dewarpedDir))
        self.assertTrue(os.path.exists(dewarpedDir))
        self.assertDictEqual(self.dewarpProcessor.getStatus(), {'percentage': 100, 'status': 'ready'})

if __name__ == '__main__':
    unittest.main()
