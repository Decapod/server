import sys
import os
import unittest
import simplejson as json

sys.path.append(os.path.abspath('..'))
from status import status, StatusTypeError, StatusFormatError
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

def loadStatusFile(statusFile):
    stFile = open(statusFile)
    status = json.load(stFile)
    stFile.close()
    return status
        
class TestStatus(unittest.TestCase):
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        
    def test_01_init(self):
        defaultStatus = {"status": "ready"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertTrue(os.path.exists(statusFile))
        self.assertDictEqual(defaultStatus, st.status)
        self.assertDictEqual(defaultStatus, loadStatusFile(statusFile))
        
    def test_02_init_defaultState(self):
        defaultStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile, "none")
        self.assertTrue(os.path.exists(statusFile))
        self.assertDictEqual(defaultStatus, st.status)
        self.assertDictEqual(defaultStatus, loadStatusFile(statusFile))
        
    def test_03_init_statusFilePathError(self):
        statusFile = os.path.join(TEST_DIR, "invalidDir", "status.json")
        self.assertRaises(IOError, status, statusFile)
    
    def test_04_init_existingStatusFile(self):
        initialStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        utils.writeToFile(json.dumps(initialStatus), statusFile)
        st = status(statusFile)
        self.assertTrue(os.path.exists(statusFile))
        self.assertDictEqual(initialStatus, st.status)
        self.assertDictEqual(initialStatus, loadStatusFile(statusFile))
        
    def test_05_set(self):
        newStatus = initialStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.set(newStatus)
        self.assertDictEqual(newStatus, st.status)
        self.assertDictEqual(newStatus, loadStatusFile(statusFile))
        
    def test_06_set_statusNotEmpty(self):
        status1 = initialStatus = {"status": "none"}
        status2 = initialStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.status = status1
        st.set(status2)
        self.assertDictEqual(status2, st.status)
        self.assertDictEqual(status2, loadStatusFile(statusFile))
  
    def test_07_set_notDictionary(self):
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertRaises(StatusTypeError, st.set, "status: none")
        
    def test_08_set_noStatusKey(self):
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertRaises(StatusFormatError, st.set, {"url": "localhost"})
        
    def test_09_update(self):
        status1 = initialStatus = {"status": "none", "url": "localhost"}
        status2 = initialStatus = {"status": "complete"}
        expectedStatus = {"status": "complete", "url": "localhost"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.status = status1
        st.update(status2)
        self.assertDictEqual(expectedStatus, st.status)
        self.assertDictEqual(expectedStatus, loadStatusFile(statusFile))
        
    def test_10_update_emptyStatus(self):
        newStatus = initialStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.update(newStatus)
        self.assertDictEqual(newStatus, st.status)
        self.assertDictEqual(newStatus, loadStatusFile(statusFile))
        
    def test_11_delKey(self):
        status1 = initialStatus = {"status": "none", "url": "localhost"}
        status2 = initialStatus = {"status": "none"}
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.status = status1
        st.delKey("url")
        self.assertDictEqual(status2, st.status)
        self.assertDictEqual(status2, loadStatusFile(statusFile))
        
    def test_12_delKey_noKey(self):
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertRaises(KeyError, st.delKey, "url")
        
    def test_13_inState(self):
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertTrue(st.inState("ready"))
        self.assertFalse(st.inState("complete"))
        
    def test_14_str(self):
        status1 = {"status": "none"}
        statusSTR = '{"status": "none"}'
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        st.status = status1
        self.assertEquals(statusSTR, str(st))
        
    def test_15_str_emptyStatus(self):
        statusSTR = '{"status": "ready"}'
        statusFile = os.path.join(TEST_DIR, "status.json")
        st = status(statusFile)
        self.assertEquals(statusSTR, str(st))
  
if __name__ == '__main__':
    unittest.main()
