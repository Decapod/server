import cherrypy
from cherrypy.test import helper
import os
import sys
sys.path.append(os.path.abspath('..'))
import decapod
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data")
LIBRARY_DIR = os.path.join(DATA_DIR, "library")
BOOK_DIR = os.path.join(LIBRARY_DIR, "book")

CONFIG = {
    "/": {
        "tools.staticdir.root": os.getcwd(),
        "request.dispatch": cherrypy.dispatch.MethodDispatcher()
    },
    "/lib": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../decapod-ui/lib"
    },
    "/components": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../decapod-ui/components"
    },
    "/shared": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../decapod-ui/shared"
    },
    "/library": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": LIBRARY_DIR
    },
    "/mockImages": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../mock-images"
    }
}

def setup_server():
    decapod.mountApp(CONFIG)
    
def teardown_server():
    utils.rmTree(BOOK_DIR)

class ServerTestCase(helper.CPWebCase):
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

class TestRoot(ServerTestCase):
    rootURL = "/"
    expectedRedirectURL = "/components/import/html/Import-05a.html"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def test_01_get(self):
        self.getPage(self.rootURL)
        self.assertStatus(303, "Should return a 303 'See Other' status for the redirect")
        self.assertHeader("Location", cherrypy.url(self.expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.rootURL, ["PUT", "POST", "DELETE"])
        
    def test_03_redirectURL(self):
        self.getPage(self.expectedRedirectURL)
        self.assertStatus(200, "Should return a 200 'OK' status")

class TestLibrary(ServerTestCase):
    libraryURL = "/library/"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.libraryURL, ["GET", "PUT", "POST", "DELETE"])

class TestBook(ServerTestCase):
    bookURL = "/library/bookName/"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        utils.makeDirs(BOOK_DIR)
    
    def tearDown(self):
        utils.rmTree(BOOK_DIR)
    
    # TODO: Test response status  
    def test_01_delete(self):
        self.assertTrue(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.getPage(self.bookURL, method="DELETE")
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
    
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.bookURL, ["GET", "PUT", "POST"])

# TODO: Test Post (including: file saved, response code, returned url)
class TestPages(ServerTestCase):
    pageURL = "/library/bookName/pages"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.pageURL, ["GET", "PUT", "DELETE"])
        
# TODO: Test put method, the trouble is that it is asynchronous       
class TestExistingExport(ServerTestCase):
    exportURL = "/library/bookName/export"
    exportStatus = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
    deleteStatus = '{"status": "none"}'
    pdfDir = os.path.join(BOOK_DIR, "images/pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    pdf = os.path.join(pdfDir, "Decapod.pdf")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        pdfSRC = os.path.abspath("data/pdf/Decapod.pdf")
        utils.makeDirs(self.pdfDir)
        utils.makeDirs(self.pdf)
        utils.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200, "Should return a 200 'OK' status")
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    # TODO: Test response status 
    def test_02_delete(self):
        self.assertTrue(os.path.exists(self.pdf), "The Decapod.pdf file should exist at path ({0})".format(self.pdf))
        self.getPage(self.exportURL, method="DELETE")
#        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.deleteStatus)
        self.assertFalse(os.path.exists(self.pdf), "The Decapod.pdf file should no longer exist at path ({0})".format(self.pdf))
    
    def test_03_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
            
class TestInProgressExport(ServerTestCase):
    exportURL = "/library/bookName/export"
    exportStatus = '{"status": "in progress"}'
    pdfDir = os.path.join(BOOK_DIR, "images/pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        utils.makeDirs(self.pdfDir)
        utils.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200, "Should return a 200 'OK' status")
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    # TODO: Test response status 
    def test_02_delete(self):
        self.getPage(self.exportURL, method="DELETE")
    
    # TODO: Test response status
    def test_03_put(self):
        self.getPage(self.exportURL, method="PUT")
    
    def test_04_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
        
# TODO: Test put method, the trouble is that it is asynchronous       
class TestNewExport(ServerTestCase):
    exportURL = "/library/bookName/export"
    exportStatus = '{"status": "none"}'
    pdfDir = os.path.join(BOOK_DIR, "images/pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        utils.makeDirs(self.pdfDir)
        utils.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200, "Should return a 200 'OK' status")
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    # TODO: Test response status 
    def test_02_delete(self):
        self.getPage(self.exportURL, method="DELETE")
#        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    def test_03_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
        
if __name__ == '__main__':
    import nose
    nose.runmodule()
