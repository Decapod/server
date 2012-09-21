import sys
import os
import unittest

sys.path.append(os.path.abspath('..'))
from firer import Firer

class firerTests(unittest.TestCase):
        
    def test_01_init(self):
        firer = Firer()
        self.assertDictEqual({}, firer.listeners)
        
    def test_02_addListener(self):
        firer = Firer()
        name = "testFirer"
        def testFirer(self): pass
        firer.addListener(name, testFirer)
        self.assertTrue(name in firer.listeners)
        self.assertEquals(testFirer, firer.listeners[name])
        
    def test_03_removeListener(self):
        firer = Firer()
        name = "testFirer"
        def testFirer(self): pass
        firer.addListener(name, testFirer)
        firer.removeListener(name)
        self.assertDictEqual({}, firer.listeners)
        
    def test_04_fire_args(self):
        firer = Firer()
        name = "testFirer"
        firedVal = "expected"
        def testFirer(val):
            self.assertEquals(firedVal, val)
        firer.addListener(name, testFirer)
        firer.fire(firedVal)
        
    def test_05_fire_kwargs(self):
        firer = Firer()
        name = "testFirer"
        firedVal = "expected"
        def testFirer(val=""):
            self.assertEquals(firedVal, val)
        firer.addListener(name, testFirer)
        firer.fire(val=firedVal)
        
if __name__ == '__main__':
    unittest.main()
