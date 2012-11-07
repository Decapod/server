import sys
import os
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import calibrator
from utils import io
import mockClasses

DATA_DIR = os.path.abspath("data/")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

MOCK_DATA_DIR = os.path.abspath("mockData/")

class TestCalibrateProcessor(unittest.TestCase):

    status_complete = {"status": "complete"}
    status_inProgress = {"status": "in progress"}
    status_ready = {"status": "ready"}
    status_error = {"status": "error"}
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
        self.calibrator = calibrator.Calibrator(DATA_DIR, STATUS_FILE, True)
        
    def tearDown(self):
        io.rmTree(DATA_DIR)
        self.calibrator = None
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        readStatus = io.loadJSONFile(statusFile)
        self.assertDictEqual(status, readStatus)
            
    def test_01_init(self):
        self.assertEquals(DATA_DIR, self.calibrator.dataDir)
        self.assertTrue(os.path.exists(self.calibrator.dataDir))
        
        self.assertEquals(STATUS_FILE, self.calibrator.statusFilePath)
        self.assertEquals(os.path.join(DATA_DIR, "unpacked"), self.calibrator.unpackedDir)
        self.assertEquals(os.path.join(DATA_DIR, "calibration"), self.calibrator.calibrationDir)
        self.assertEquals(os.path.join(DATA_DIR, "calibration.zip"), self.calibrator.export)
        
        self.assertDictEqual(self.status_ready, self.calibrator.status.model)
            
    def test_02_init_statusFile(self):
        io.writeToJSONFile(self.status_inProgress, STATUS_FILE)
        self.calibrator = calibrator.Calibrator(DATA_DIR, STATUS_FILE)
        self.assertDictEqual(self.status_inProgress, self.calibrator.status.model)
        self.assertStatusFile(self.status_inProgress, self.calibrator.statusFilePath)
        
    def test_03_getStatus(self):
        status = self.calibrator.getStatus()
        self.assertDictEqual(status, self.calibrator.status.model)
        self.assertDictEqual(status, self.status_ready)
        
    def test_04_getImagesStatus(self):
        self.assertRaises(calibrator.UnpackedDirNotExistError, self.calibrator.getImagesStatus)

        io.makeDirs(self.calibrator.unpackedDir)
        io.makeDirs(self.calibrator.calibrationDir)
        status = self.calibrator.getImagesStatus()
        self.assertEqual(status["ERROR_CODE"], "NO_STEREO_IMAGES")
        
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.calibrator.calibrationDir, "capture-0_1.jpg"))
        status = self.calibrator.getImagesStatus()
        self.assertEqual(status["ERROR_CODE"], "NO_STEREO_IMAGES")

        for i in range(0, calibrator.REQUIRED_STEREO_IMAGES -1):
            shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.calibrator.unpackedDir, "capture-{0}_1.jpg".format(i)))
            shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.calibrator.unpackedDir, "capture-{0}_2.jpg".format(i)))
        status = self.calibrator.getImagesStatus()
        self.assertEqual(status["ERROR_CODE"], "NOT_ENOUGH_IMAGES")
        self.assertEqual(status["requiredStereoImages"], calibrator.REQUIRED_STEREO_IMAGES)
        self.assertEqual(status["DetectedStereoImages"], calibrator.REQUIRED_STEREO_IMAGES - 1)

        for i in range(calibrator.REQUIRED_STEREO_IMAGES -1, calibrator.REQUIRED_STEREO_IMAGES):
            shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.calibrator.unpackedDir, "capture-{0}_1.jpg".format(i)))
            shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_2.jpg"), os.path.join(self.calibrator.unpackedDir, "capture-{0}_2.jpg".format(i)))
        status = self.calibrator.getImagesStatus()
        self.assertEqual(status["numOfStereoImages"], calibrator.REQUIRED_STEREO_IMAGES)
        
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), os.path.join(self.calibrator.calibrationDir, "capture-a_1.jpg"))
        status = self.calibrator.getImagesStatus()
        self.assertEqual(status["numOfStereoImages"], calibrator.REQUIRED_STEREO_IMAGES)
        
    def test_05_isInState(self):
        states = ["complete", "in progress", "ready"]
        for state in states:
            self.calibrator.status.update("status", state)
            self.assertTrue(self.calibrator.isInState(state))
    
    def test_06_isInState_false(self):
        self.assertFalse(self.calibrator.isInState("test"))
    
    def test_07_delete(self):
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), self.calibrator.export)
        io.makeDirs(self.calibrator.calibrationDir)
        self.calibrator.status.update("status", "complete")
        
        self.assertTrue(os.path.exists(self.calibrator.calibrationDir))
        self.assertTrue(os.path.exists(self.calibrator.export))

        self.calibrator.delete()
        self.assertTrue(os.path.exists(self.calibrator.dataDir))
        self.assertTrue(os.path.exists(self.calibrator.statusFilePath))
        self.assertFalse(os.path.exists(self.calibrator.calibrationDir))
        self.assertFalse(os.path.exists(self.calibrator.export))
        self.assertDictEqual(self.status_ready, self.calibrator.status.model)
        self.assertStatusFile(self.status_ready, self.calibrator.statusFilePath)
    
    def test_08_delete_inProgress(self):
        self.calibrator.status.update("status", "in progress")
        self.assertRaises(calibrator.CalibrateInProgressError, self.calibrator.deleteUpload)
    
    def test_09_deleteUpload(self):
        self.calibrator.status.update("status", "complete")
        io.makeDirs(self.calibrator.unpackedDir)
        self.assertTrue(os.path.exists(self.calibrator.unpackedDir))
        self.calibrator.deleteUpload()
        self.assertFalse(os.path.exists(self.calibrator.unpackedDir))
    
    def test_10_deleteUpload_inProgress(self):
        self.calibrator.status.update("status", "in progress")
        self.assertRaises(calibrator.CalibrateInProgressError, self.calibrator.delete)
    
    def test_11_unzip_inProgress(self):
        self.calibrator.status.update("status", "in progress")
        self.assertRaises(calibrator.CalibrateInProgressError, self.calibrator.unzip, "mock")
        
    def test_12_unzip_badZip(self):
        io.makeDirs(self.calibrator.unpackedDir)
        origFilePath = os.path.join(self.calibrator.dataDir, "capture-0_1.jpg")
        shutil.copyfile(os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), origFilePath)
        testFile = mockClasses.mockFileStream(origFilePath)
        status = self.calibrator.unzip(os.path.join(testFile))
        self.assertEqual(status["ERROR_CODE"], "BAD_ZIP")

    def prepareCalibrate(self):
        io.makeDirs(self.calibrator.unpackedDir)
#        
    def test_13_calibrate_exceptions(self):
        self.assertRaises(calibrator.UnpackedDirNotExistError, self.calibrator.calibrate)

    def test_14_calibrate_inProgress(self):
        self.prepareCalibrate()
        self.calibrator.status.update("status", "in progress")
        self.assertRaises(calibrator.CalibrateInProgressError, self.calibrator.calibrate)

    def test_15_calibrate(self):
        self.prepareCalibrate()
        self.calibrator.calibrate()
        self.assertTrue(os.path.exists(self.calibrator.calibrationDir))
        self.assertTrue(os.path.exists(self.calibrator.export))
        self.assertDictEqual(self.status_complete, self.calibrator.status.model)

if __name__ == '__main__':
    unittest.main()
