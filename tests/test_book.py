import sys
import os
import unittest
import shutil

import testutils
sys.path.append(os.path.abspath('..'))
import book

BOOK_DIR = os.path.abspath("data/library/book/")

class TestBookExisting(unittest.TestCase):
    
    resources = None
    book = None
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()
        self.book = book.Book(self.resources)
        if not os.path.exists(BOOK_DIR):
            os.makedirs(BOOK_DIR)
    
    def test_01_delete(self):
        self.assertTrue(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.book.delete()
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))

class TestBookNone(unittest.TestCase):
    
    resources = None
    book = None
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()
        self.book = book.Book(self.resources)
        if os.path.exists(BOOK_DIR):
            shutil.rmtree(BOOK_DIR)
            
    def test_01_delete(self):
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
        self.book.delete()
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
   