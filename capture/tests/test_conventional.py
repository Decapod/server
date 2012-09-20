import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import conventional
#from mockClasses import mockResourceSource
from utils import io

CONVENTIONAL_DIR = os.path.abspath(os.path.join("data", "conventional"))
CAPTURE_STATUS_FILENAME = "captureStatus.json"

class TestConventional(unittest.TestCase):
    
    conventional = None
    
    def setUp(self):
        self.conventional = conventional.Conventional(CONVENTIONAL_DIR, CAPTURE_STATUS_FILENAME, True)
    
    def tearDown(self):
        io.rmTree(CONVENTIONAL_DIR)
        
    def test_01_init(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))

    def test_02_capture(self):
        expected = ["./mockData/images/1.jpg", "./mockData/images/2.jpg"]
        
        self.assertListEqual(self.conventional.capture(), expected)
        
    def test_03_delete(self):
        self.conventional.delete()
        self.assertFalse(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should have been removed".format(CONVENTIONAL_DIR))

#class TestBookNone(unittest.TestCase):
#    
#    book = None
#    mockRS = mockResourceSource({"/library": {"path": BOOK_DIR}})
#    
#    def setUp(self):
#        self.book = book.Book(self.mockRS)
#        io.rmTree(BOOK_DIR)
#            
#    def test_01_delete(self):
#        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
#        self.book.delete()
#        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))

if __name__ == '__main__':
    unittest.main()