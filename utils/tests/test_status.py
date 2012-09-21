import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
from mockClasses import mockStore
from status import Status

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

class TestStatus(unittest.TestCase):
    
    def setUp(self):
        self.statusModel = {"test": "test"}
        
    def tearDown(self):
        self.statusModel = None
    
    def test_01_init_emptyStore_defaultModel(self):
        store = mockStore()
        status = Status(store)
        self.assertDictEqual({}, status.model)
        self.assertIsNone(store.stored)
        
    def test_02_init_store_defaultModel(self):
        store = mockStore(self.statusModel)
        status = Status(store)
        self.assertDictEqual(self.statusModel, status.model)
        self.assertDictEqual(self.statusModel, store.stored)
        
    def test_03_init_emptyStore(self):
        store = mockStore()
        status = Status(store, self.statusModel)
        self.assertDictEqual(self.statusModel, status.model)
        self.assertIsNone(store.stored)
        
    def test_04_init_store(self):
        initialStored = {"a": "a"}
        expected = {"a": "a", "test": "test"}
        store = mockStore(initialStored)
        status = Status(store, self.statusModel)
        self.assertDictEqual(expected, status.model)
        self.assertDictEqual(expected, self.statusModel)
        self.assertDictEqual(initialStored, store.stored)
        
    def test_05_update(self):
        expected = {"a": "a", "test": "TEST"}
        store = mockStore()
        status = Status(store, self.statusModel)
        status.update("a", "a");
        status.update("test", "TEST")
        self.assertDictEqual(expected, status.model)
        self.assertDictEqual(expected, self.statusModel)
        
    def test_05_remove(self):
        expected = {}
        store = mockStore()
        status = Status(store, self.statusModel)
        status.remove("test");
        self.assertDictEqual(expected, status.model)
        self.assertDictEqual(expected, self.statusModel)
        
    def test_06_listener_update(self):
        expected = {"test": "TEST"}
        store = mockStore()
        status = Status(store, self.statusModel)
        def testUpdate(**kwargs):
            self.assertDictEqual(expected, kwargs["newModel"])
        status.applier.onModelChanged.addListener("testUpdate", testUpdate)
        status.update("test", "TEST")
        
    def test_07_listener_remove(self):
        expected = {}
        store = mockStore()
        status = Status(store, self.statusModel)
        def testRemove(**kwargs):
            self.assertDictEqual(expected, kwargs["newModel"])
        status.applier.onModelChanged.addListener("testRemove", testRemove)
        status.remove("test")
        
if __name__ == '__main__':
    unittest.main()
