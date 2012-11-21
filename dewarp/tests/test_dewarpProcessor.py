import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
sys.path.append(os.path.abspath(os.path.join('..', '..', '..', 'decapod-dewarping')))
import dewarpProcessor
from utils import io
import mockClasses

DATA_DIR = os.path.abspath("data/")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

MOCK_DATA_DIR = os.path.abspath("mockData/")

class TestDewarpProcessor(unittest.TestCase):

    status_complete = {"status": "complete"}
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

        # Test unmatched paris error
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_2.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-1_1.jpg"))
        
        status = self.dewarpProcessor.getCapturesStatus()
        self.assertEqual(status["ERROR_CODE"], "UnmatchedPairs")
        self.assertListEqual(status["msg"], ["capture-1_1.jpg"])
        
        io.rmFile(os.path.join(self.dewarpProcessor.unpackedDir, "capture-1_1.jpg"))
        self.assertDictEqual(self.dewarpProcessor.getCapturesStatus(), {"numOfCaptures": 1})
        
    def test_05_getCalibrationStatus(self):
        self.assertRaises(dewarpProcessor.CalibrationDirNotExistError, self.dewarpProcessor.getCalibrationStatus)

    def test_06_getCalibrationStatus_invalid(self):
        io.makeDirs(self.dewarpProcessor.calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(self.dewarpProcessor.calibrationDir, "calibration.xml"))
        status = self.dewarpProcessor.getCalibrationStatus()
        self.assertEqual(status["ERROR_CODE"], "INVALID_CALIBRATION")
        
    def test_07_getCalibrationStatus_invalid(self):
        io.makeDirs(self.dewarpProcessor.calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(self.dewarpProcessor.calibrationDir, "calibration.xml"))
        status = self.dewarpProcessor.getCalibrationStatus()
        self.assertEqual(status["ERROR_CODE"], "INVALID_CALIBRATION")
        
    def test_08_getCalibrationStatus_valid(self):
        shutil.copytree(os.path.join(MOCK_DATA_DIR, "valid-calibration"), self.dewarpProcessor.calibrationDir)
        status = self.dewarpProcessor.getCalibrationStatus()
        self.assertEqual(status, None)
        
    def test_09_isInState(self):
        states = ["complete", "in progress", "ready"]
        for state in states:
            self.dewarpProcessor.status.update("status", state)
            self.assertTrue(self.dewarpProcessor.isInState(state))
    
    def test_10_isInState_false(self):
        self.assertFalse(self.dewarpProcessor.isInState("test"))
    
    def test_11_delete(self):
        io.makeDirs(self.dewarpProcessor.dewarpedDir)
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), self.dewarpProcessor.export)
        self.dewarpProcessor.status.update("status", "complete")

        self.assertTrue(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.export))

        self.dewarpProcessor.delete()
        self.assertTrue(os.path.exists(self.dewarpProcessor.dataDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.statusFilePath))
        self.assertFalse(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertFalse(os.path.exists(self.dewarpProcessor.export))
        self.assertDictEqual(self.status_ready, self.dewarpProcessor.status.model)
        self.assertStatusFile(self.status_ready, self.dewarpProcessor.statusFilePath)
    
    def test_12_delete_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.delete)
    
    def test_13_deleteCalibrationUpload(self):
        self.dewarpProcessor.status.update("status", "complete")
        io.makeDirs(self.dewarpProcessor.calibrationDir)
        self.assertTrue(os.path.exists(self.dewarpProcessor.calibrationDir))
        self.dewarpProcessor.deleteCalibrationUpload()
        self.assertFalse(os.path.exists(self.dewarpProcessor.calibrationDir))
    
    def test_14_deleteCalibrationUpload_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.deleteCalibrationUpload)
    
    def test_15_deleteCapturesUpload(self):
        self.dewarpProcessor.status.update("status", "complete")
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        self.assertTrue(os.path.exists(self.dewarpProcessor.unpackedDir))
        self.dewarpProcessor.deleteCapturesUpload()
        self.assertFalse(os.path.exists(self.dewarpProcessor.unpackedDir))
    
    def test_16_deleteCapturesUpload_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.deleteCapturesUpload)
    
    def test_17_unzip_badZip(self):
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        origFilePath = os.path.join(self.dewarpProcessor.dataDir, "capture-0_1.jpg")
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), origFilePath)
        testFile = mockClasses.mockFileStream(origFilePath)
        status = self.dewarpProcessor.unzip(os.path.join(testFile), "mock")
        self.assertEqual(status["ERROR_CODE"], "BAD_ZIP")

    def test_18_unzipCalibration_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.unzipCalibration, "mock")
        
    def test_19_unzipCaptures_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.unzipCaptures, "mock")
        
    def prepareDewarp(self):
        io.makeDirs(self.dewarpProcessor.unpackedDir)
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_1.jpg"))
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.dewarpProcessor.unpackedDir, "capture-0_2.jpg"))

        io.makeDirs(self.dewarpProcessor.calibrationDir)
        shutil.copy(os.path.join(MOCK_DATA_DIR, "calibration", "calibration.xml"), os.path.join(self.dewarpProcessor.calibrationDir, "calibration.xml"))
        
    def test_20_dewarpImp_exceptions(self):
        self.assertRaises(dewarpProcessor.CalibrationDirNotExistError, self.dewarpProcessor.dewarpImp, "mock1", "mock2", "mock3")
        io.makeDirs(self.dewarpProcessor.calibrationDir)
        self.assertRaises(dewarpProcessor.UnpackedDirNotExistError, self.dewarpProcessor.dewarpImp, self.dewarpProcessor.calibrationDir, "mock2", "mock3")

    def test_21_dewarpImp(self):
        self.prepareDewarp()
        self.assertTrue(self.dewarpProcessor.dewarpImp(self.dewarpProcessor.calibrationDir, self.dewarpProcessor.unpackedDir, self.dewarpProcessor.dewarpedDir))
        self.assertTrue(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.dewarpProcessor.getStatus(), {'currentCapture': 1, 'numOfCaptures': 1, 'status': 'ready'})

    def test_22_dewarp_inProgress(self):
        self.dewarpProcessor.status.update("status", "in progress")
        self.assertRaises(dewarpProcessor.DewarpInProgressError, self.dewarpProcessor.dewarp)

    def test_23_dewarp_exception(self):
        self.assertRaises(dewarpProcessor.DewarpError, self.dewarpProcessor.dewarp)
        self.assertFalse(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.status_error, self.dewarpProcessor.status.model)

    def test_24_dewarp(self):
        self.prepareDewarp()
        self.dewarpProcessor.dewarp()
        self.assertTrue(os.path.exists(self.dewarpProcessor.dewarpedDir))
        self.assertDictEqual(self.status_complete, self.dewarpProcessor.status.model)

if __name__ == '__main__':
    unittest.main()
