import cherrypy
from cherrypy.test import helper
import shutil
import os
import sys
sys.path.append(os.path.abspath('..'))
import decapod

    # Decapod 0.5 REST URL Spec 
    #    /: GET
    #    /library/: NONE
    #    /library/'bookName': DELETE
    #    /library/'bookName'/pages: POST
    #    /library/'bookName'/export: GET, PUT, DELETE

BOOK_DIR = os.path.normpath(os.path.join(os.getcwd(), "../library/book"))

def setup_server():
    decapod.mountApp()
    
def teardown_server():
    if os.path.exists(BOOK_DIR):
        shutil.rmtree(BOOK_DIR)
        os.mkdir(BOOK_DIR)

class serverTests(helper.CPWebCase):
    '''
    A subclass of helper.CPWebCase
    The purpose of this class is to add new common test functions that can be easily shared
    by various test classes.
    '''
    def assertUnsupportedHTTPMethods(self, url, methods):
        '''
        Tests that unsuppored http methods return a 405
        '''     
        for method in methods:
            self.getPage(url, method=method)
            self.assertStatus(405, "Should return a 405 'Method not Allowed' status for '{0}'".format(method))

class TestRoot(serverTests):
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    rootURL = "/"
    expectedRedirectURL = "/components/import/html/Import-05a.html"
    
    def test_01_get(self):
        self.getPage(self.rootURL)
        self.assertStatus(303, "Should return a 303 'See Other' status for the redirect")
        self.assertHeader("Location", cherrypy.url(self.expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.rootURL, ["PUT", "POST", "DELETE"])
        
    def test_03_redirectURL(self):
        self.getPage(self.expectedRedirectURL)
        self.assertStatus(200, "Should return a 200 'OK' status")

class TestLibrary(serverTests):
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        libraryURL = "/library/"
        self.assertUnsupportedHTTPMethods(libraryURL, ["GET", "PUT", "POST", "DELETE"])

class TestBook(serverTests):
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    # TODO: Tests that something existed before the deletion
    def test_01_book(self):
        bookURL = "/library/bookName/"
        self.assertTrue(BOOK_DIR, "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.getPage(bookURL, method="DELETE")
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
        self.assertUnsupportedHTTPMethods(bookURL, ["GET", "PUT", "POST"])
        
        
