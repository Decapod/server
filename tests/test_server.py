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

class TestREST(helper.CPWebCase):
    
    def setup_server():
        if not os.path.exists(BOOK_DIR):
            os.mkdir(BOOK_DIR)
        decapod.mountApp()
    setup_server = staticmethod(setup_server)
    
    def teardown_server():
        if os.path.exists(BOOK_DIR):
            shutil.rmtree(BOOK_DIR)
            os.mkdir(BOOK_DIR)
    teardown_server = staticmethod(teardown_server)
    
    def unsupportedHTTPMethodsTest(self, url, methods):
        '''
        Tests that unsuppored http methods return a 405
        '''     
        for method in methods:
            self.getPage(url, method=method)
            self.assertStatus(405, "Should return a 405 'Method not Allowed' status for '{0}'".format(method))
     
    def test_01_root(self):
        rootURL = "/"
        expectedRedirectURL = "/components/import/html/Import-05a.html"
        self.getPage(rootURL)
        self.assertStatus(303, "Should return a 303 'See Other' status for the redirect")
        self.assertHeader("Location", cherrypy.url(expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        self.unsupportedHTTPMethodsTest(rootURL, ["PUT", "POST", "DELETE"])
        
    def test_02_redirectURL(self):
        expectedRedirectURL = "/components/import/html/Import-05a.html"
        self.getPage(expectedRedirectURL)
        self.assertStatus(200, "Should return a 200 'OK' status")
        
    def test_03_library(self):
        libraryURL = "/library/"
        self.unsupportedHTTPMethodsTest(libraryURL, ["GET", "PUT", "POST", "DELETE"])
        
    # TODO: Tests that something existed before the deletion
    def test_04_book(self):
        bookURL = "/library/bookName/"
        self.assertTrue(BOOK_DIR, "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.getPage(bookURL, method="DELETE")
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
        self.unsupportedHTTPMethodsTest(bookURL, ["GET", "PUT", "POST"])
        
        
