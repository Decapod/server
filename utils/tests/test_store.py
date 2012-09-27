import sys
import os
import unittest
import simplejson as json

sys.path.append(os.path.abspath('..'))
import store
from utils import io

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "testDir")

class FSStoreTests(unittest.TestCase):

    def setUp(self):
        io.makeDirs(TEST_DIR)
        self.filePath = os.path.join(TEST_DIR, "one_more_level", "sample.json")
        self.jsonData = {"test": "test"}
        
        self.fsstore = store.FSStore(self.filePath)
        
    def tearDown(self):
        io.rmTree(TEST_DIR)
        
    def test_01_getNotExists(self):
         content = self.fsstore.load()
         self.assertIsNone(content, "The retrieval on an non-existent file returns None.")
        
    def test_02_getExists(self):
        io.writeToFile(json.dumps(self.jsonData), self.filePath)
        content = self.fsstore.load()
        self.assertDictEqual(self.jsonData, content)
        
    def test_03_setNotExists(self):
        self.fsstore.save(self.jsonData)
        readContent = io.readFromFile(self.filePath)
        self.assertEquals(readContent, json.dumps(self.jsonData))
        
    def test_04_setExists(self):
        randomStr = "This is a random test string"
        io.writeToFile(randomStr, self.filePath)
        self.fsstore.save(self.jsonData)
        readContent = io.readFromFile(self.filePath)
        self.assertEquals(readContent, json.dumps(self.jsonData))
        
if __name__ == '__main__':
    unittest.main()
