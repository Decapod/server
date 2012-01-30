import sys
import os
import unittest

import testutils
sys.path.append(os.path.abspath('..'))
import book
import decapod_utilities as utils

LIBRARY_PATH = os.path.abspath("data/library/")
BOOK_DIR = os.path.join(LIBRARY_PATH, "book")

class TestBookExisting(unittest.TestCase):
    
    book = None
    mockRS = testutils.mockResourceSource({"/library": {"path": LIBRARY_PATH}})
    
    def setUp(self):
        self.book = book.Book(self.mockRS)
        utils.makeDirs(BOOK_DIR)
    
    def test_01_delete(self):
        self.assertTrue(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.book.delete()
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))

class TestBookNone(unittest.TestCase):
    
    book = None
    mockRS = testutils.mockResourceSource({"/library": {"path": BOOK_DIR}})
    
    def setUp(self):
        self.book = book.Book(self.mockRS)
        utils.rmTree(BOOK_DIR)
            
    def test_01_delete(self):
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
        self.book.delete()
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))

if __name__ == '__main__':
    unittest.main()