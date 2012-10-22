import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import dewarpProcessor
from utils import io
import mockClasses

DATA_DIR = os.path.abspath("data/")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

MOCK_DATA_DIR = os.path.abspath("mockData/")

class TestDewarpProcessor(unittest.TestCase):

    status_complete = {"status": "complete", "percentage": 100, "currentCapture": 1}
    status_inProgress = {"status": "in progress", "percentage": 0, "currentCapture": 0}
    status_ready = {"status": "ready"}
    status_error = {"status": "error"}
    
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
        self.assertEquals(os.path.join(DATA_DIR, "unpacked"), self.dewarpProcessor.unpackedDir)
        self.assertEquals(os.path.join(DATA_DIR, "dewarped"), self.dewarpProcessor.dewarpedDir)
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
        
    def test_04_getCapturesStatus(self):
        self.assertRaises(dewarpProcessor.UnpackedDirNotExistError, self.dewarpProcessor.getCapturesStatus)

        io.makeDirs(self.dewarpProcessor.unpackedDir)
        status = self.dewarpProcessor.getCapturesStatus()
        self.assertEqual(status["ERROR_CODE"], "CalibrationDirNotExist")
        
        io.makeDirs(self.dewarpProcessor.calibrationDir)
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.calibrationDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.dewarpProcessor.calibrationDir, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.calibrationDir, "capture-1_1.jpg"))
        
        status = self.dewarpProcessor.getCapturesStatus()
        self.assertEqual(status["ERROR_CODE"], "UnmatchedPairs")
        self.assertListEqual(status["msg"], ["capture-1_1.jpg"])
        
        io.rmFile(os.path.join(self.dewarpProcessor.calibrationDir, "capture-1_1.jpg"))
        self.assertDictEqual(self.dewarpProcessor.getCapturesStatus(), {"numOfCaptures": 1})
        
    def test_05_isInState(self):
        states = ["complete", "in progress", "ready"]
        for state in states:
            self.dewarpProcessor.status.update("status", state)
            self.assertTrue(self.dewarpProcessor.isInState(state))
    
    def test_06_isInState_false(self):
        self.assertFalse(self.dewarpProcessor.isInState("test"))
    
    def test_07_delete(self):
        self.dewarpProcessor.status.update("status", "complete")
        self.dewarpProcessor.delete()
        self.assertTrue(os.path.exists(self.dewarpProcessor.dataDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.statusFilePath))
        self.assertFalse(os.path.exists(self.dewarpProcessor.unpackedDir))
        self.assertFalse(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertFalse(os.path.exists(self.dewarpProcessor.export))
        self.assertDictEqual(self.status_ready, self.dewarpProcessor.status.model)
        self.assertStatusFile(self.status_ready, self.dewarpProcessor.statusFilePath)
    
    def test_08_delete_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.deleteUpload)
    
    def test_09_deleteUpload(self):
        self.dewarpProcessor.status.update("status", "complete")
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        self.assertTrue(os.path.exists(self.dewarpProcessor.unpackedDir))
        self.dewarpProcessor.deleteUpload()
        self.assertFalse(os.path.exists(self.dewarpProcessor.unpackedDir))
    
    def test_10_deleteUpload_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.delete)
    
    def test_11_unzip_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.unzip, "mock")
        
    def test_12_unzip_badZip(self):
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        origFilePath = os.path.join(self.dewarpProcessor.dataDir, "capture-0_1.jpg")
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), origFilePath)
        testFile = mockClasses.mockFileStream(origFilePath)
        status = self.dewarpProcessor.unzip(os.path.join(testFile))
        self.assertEqual(status["ERROR_CODE"], "BadZip")

    def test_13_findPairs(self):
        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-1_1.jpg"))
        
        matched, unmatched = self.dewarpProcessor.findPairs(DATA_DIR)
        self.assertEqual(matched, [(os.path.join(DATA_DIR, "capture-0_1.jpg"), os.path.join(DATA_DIR, "capture-0_2.jpg"))])
        self.assertEqual(unmatched, [os.path.join(DATA_DIR, "capture-1_1.jpg")])

    def prepareDewarp(self):
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_2.jpg"))

        io.makeDirs(self.dewarpProcessor.calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(self.dewarpProcessor.calibrationDir, "calibration.xml"))
        
    def test_14_dewarpImp_exceptions(self):
        self.assertRaises(dewarpProcessor.UnpackedDirNotExistError, self.dewarpProcessor.dewarpImp, "mock1", "mock2")

    def test_15_dewarpImp(self):
        self.prepareDewarp()
        self.assertTrue(self.dewarpProcessor.dewarpImp(self.dewarpProcessor.unpackedDir, self.dewarpProcessor.dewarpedDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.dewarpProcessor.getStatus(), {'currentCapture': 1, 'percentage': 100, 'status': 'ready'})

    def test_16_dewarp_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.dewarp)

    def test_17_dewarp_exception(self):
        self.assertRaises(dewarpProcessor.DewarpError, self.dewarpProcessor.dewarp)
        self.assertFalse(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.status_error, self.dewarpProcessor.status.model)

    def test_18_dewarp(self):
        self.prepareDewarp()
        self.dewarpProcessor.dewarp()
        self.assertTrue(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.status_complete, self.dewarpProcessor.status.model)

if __name__ == '__main__':
    unittest.main()
