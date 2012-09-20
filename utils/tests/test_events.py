import sys
import os
import unittest

sys.path.append(os.path.abspath('..'))
from events import Events

class eventTests(unittest.TestCase):
        
    def test_01_init(self):
        event = Events()
        self.assertDictEqual({}, event.listeners)
        
    def test_02_addListener(self):
        event = Events()
        name = "testEvent"
        def testEvent(self): pass
        event.addListener(name, testEvent)
        self.assertTrue(name in event.listeners)
        self.assertEquals(testEvent, event.listeners[name])
        
    def test_03_removeListener(self):
        event = Events()
        name = "testEvent"
        def testEvent(self): pass
        event.addListener(name, testEvent)
        event.removeListener(name)
        self.assertDictEqual({}, event.listeners)
        
    def test_04_fire_args(self):
        event = Events()
        name = "testEvent"
        firedVal = "expected"
        def testEvent(val):
            self.assertEquals(firedVal, val)
        event.addListener(name, testEvent)
        event.fire(firedVal)
        
    def test_05_fire_kwargs(self):
        event = Events()
        name = "testEvent"
        firedVal = "expected"
        def testEvent(val=""):
            self.assertEquals(firedVal, val)
        event.addListener(name, testEvent)
        event.fire(val=firedVal)
        
if __name__ == '__main__':
    unittest.main()
