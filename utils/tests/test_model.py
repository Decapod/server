import sys
import os
import unittest

sys.path.append(os.path.abspath('..'))
import model

MODEL = {"a": "a", "b": {"c": "c"}}

class eventTests(unittest.TestCase):
    
    def setUp(self):
        self.model = MODEL.copy()
    
    def tearDown(self):
        self.model = None
    
    def test_01_getSegs(self):
        segStr = "a.b"
        segList = ["a", "b"]
        self.assertListEqual(segList, model.getSegs(segStr))
        self.assertListEqual(segList, model.getSegs(segList))
    
    def test_02_get_exists(self):
        val1 = model.get(self.model, "a")
        val2 = model.get(self.model, "b.c")
        self.assertEquals("a", val1)
        self.assertEquals("c", val2)
        
    def test_03_get_exists_list(self):
        val1 = model.get(self.model, "a")
        val2 = model.get(self.model, ["b", "c"])
        self.assertEquals("a", val1)
        self.assertEquals("c", val2)
        
    def test_04_get_not_exist(self):
        val1 = model.get(self.model, "c")
        val2 = model.get(self.model, "b.d")
        self.assertIsNone(val1)
        self.assertIsNone(val2)
        
    def test_05_get_not_exist_list(self):
        val1 = model.get(self.model, "c")
        val2 = model.get(self.model, ["b", "d"])
        self.assertIsNone(val1)
        self.assertIsNone(val2)
        
    def test_06_set_exists(self):
        model.set(self.model, "a", "A")
        model.set(self.model, "b.c", "C")
        self.assertEquals("A", self.model["a"])
        self.assertEquals("C", self.model["b"]["c"])
        
    def test_07_set_exists_list(self):
        model.set(self.model, "a", "A")
        model.set(self.model, ["b", "c"], "C")
        self.assertEquals("A", self.model["a"])
        self.assertEquals("C", self.model["b"]["c"])
        
    def test_08_set_not_exist(self):
        model.set(self.model, "d", "d")
        model.set(self.model, "b.e", "e")
        self.assertEquals("d", self.model["d"])
        self.assertEquals("e", self.model["b"]["e"])
        
    def test_09_set_not_exist(self):
        model.set(self.model, "d", "d")
        model.set(self.model, ["b", "e"], "e")
        self.assertEquals("d", self.model["d"])
        self.assertEquals("e", self.model["b"]["e"])
        
    def test_10_init(self):
        ca = model.ChangeApplier(self.model)
        self.assertDictEqual(self.model, ca.model)
        
    def test_11_requestUpdate_modify(self):
        ca = model.ChangeApplier(self.model)
        expectedReq = {"elPath": "a", "value": "A", "type": "UPDATE"}
        def testEvent(oldModel=None, newModel=None, request=None):
            self.assertDictEqual(MODEL, oldModel)
            self.assertDictEqual(self.model, newModel)
            self.assertDictEqual(expectedReq, request)
            self.assertEquals("A", newModel["a"])
        ca.onModelChanged.addListener("testEvent", testEvent)
        ca.requestUpdate("a", "A")
        
    def test_12_requestUpdate_create(self):
        ca = model.ChangeApplier(self.model)
        expectedReq = {"elPath": "c", "value": "c", "type": "UPDATE"}
        def testEvent(oldModel=None, newModel=None, request=None):
            self.assertDictEqual(MODEL, oldModel)
            self.assertDictEqual(self.model, newModel)
            self.assertDictEqual(expectedReq, request)
            self.assertEquals("c", newModel["c"])
        ca.onModelChanged.addListener("testEvent", testEvent)
        ca.requestUpdate("c", "c")
        
    def test_13_requestRemoval_exists(self):
        ca = model.ChangeApplier(self.model)
        expectedReq = {"elPath": "a", "type": "REMOVAL"}
        def testEvent(oldModel=None, newModel=None, request=None):
            self.assertDictEqual(MODEL, oldModel)
            self.assertDictEqual(self.model, newModel)
            self.assertDictEqual(expectedReq, request)
            self.assertFalse("a" in newModel)
        ca.onModelChanged.addListener("testEvent", testEvent)
        ca.requestRemoval("a")
        
    def test_14_requestRemoval_not_exist(self):
        ca = model.ChangeApplier(self.model)
        expectedReq = {"elPath": "c", "type": "REMOVAL"}
        def testEvent(oldModel=None, newModel=None, request=None):
            self.assertDictEqual(MODEL, oldModel)
            self.assertDictEqual(self.model, newModel)
            self.assertDictEqual(expectedReq, request)
            self.assertFalse("c" in newModel)
        ca.onModelChanged.addListener("testEvent", testEvent)
        ca.requestRemoval("c")
        
if __name__ == '__main__':
    unittest.main()
