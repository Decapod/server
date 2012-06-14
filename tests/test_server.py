import cherrypy
from cherrypy.test import helper
import uuid
import mimetypes
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
    }
}

def setup_server(config=CONFIG):
    decapod.mountApp(config)
    
def teardown_server(dir=BOOK_DIR):
    utils.rmTree(dir)

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
            
    def fileUploadPostParams(self, path):
        '''
        Generates the headers and body needed to POST a file upload, for the file at 'path'
        '''
        CRLF = "\r\n"
        fileName = os.path.split(path)[1]
        fileType = mimetypes.guess_type(path)[0]
        id = uuid.uuid4()
        boundary = "---------------------------" + id.hex
        
        f = open(path)
        read = f.read()
        f.close()
        
        body = '--{0}{1}Content-Disposition: form-data; name="file"; filename="{2}"{1}Content-Type: {3}{1}{1}{4}{1}--{0}--{1}'.format(boundary, CRLF, fileName, fileType, read)
        headers = [
            ("Content-Length", len(body)),
            ("Content-Type", "multipart/form-data; boundary=" + boundary),
            ("Pragma", "no-cache"),
            ("Cache-Control", "no-cache")
        ]
        
        return headers, body
    
    def uploadFile(self, url, path):
        '''
        Posts the file at 'path' to the resource at 'url'
        '''
        headers, body = self.fileUploadPostParams(path)
        self.getPage(url, headers, "POST", body)
        
class TestConfig(helper.CPWebCase):
    # hardcoding due to the fact that setup_server can't take any arguments, not even "self"
    def customServerSetup():
        setup_server({
            "global": {
                "server.socket_host": "0.0.0.0"
            }
        })
    
    setup_server = staticmethod(customServerSetup)
    tearDown = staticmethod(teardown_server)
    
    def test_01_socket_host(self):
        self.assertEquals("0.0.0.0", cherrypy.config["server.socket_host"])

class TestRoot(ServerTestCase):
    rootURL = "/"
    expectedRedirectURL = "/components/exporter/html/exporter.html"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def test_01_get(self):
        self.getPage(self.rootURL)
        self.assertStatus(301)
        self.assertHeader("Location", cherrypy.url(self.expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.rootURL, ["PUT", "POST", "DELETE"])
        
    def test_03_redirectURL(self):
        self.getPage(self.expectedRedirectURL)
        self.assertStatus(200)

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
     
    def test_01_delete(self):
        self.assertTrue(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should currently exist".format(BOOK_DIR))
        self.getPage(self.bookURL, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(BOOK_DIR), "The 'book' directory (at path: {0}) should have been removed".format(BOOK_DIR))
    
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.bookURL, ["GET", "PUT", "POST"])

class TestPages(ServerTestCase):
    pageURL = "/library/bookName/pages"
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def test_01_post_valid(self):
        self.uploadFile(self.pageURL, os.path.join(DATA_DIR, "images/Image_0015.JPEG"))
        self.assertStatus(201)
        self.assertHeader("Location")
        
    def test_02_post_invalid(self):
        self.uploadFile(self.pageURL, os.path.join(DATA_DIR, "pdf/Decapod.pdf"))
        self.assertStatus(415)
    
    def test_03_unsupportedMethods(self):
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
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    def test_02_delete(self):
        self.assertTrue(os.path.exists(self.pdf), "The Decapod.pdf file should exist at path ({0})".format(self.pdf))
        self.getPage(self.exportURL, method="DELETE")
        self.assertStatus(204)
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
        self.assertStatus(200)
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
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
     
    def test_02_delete(self):
        self.getPage(self.exportURL, method="DELETE")
        self.assertStatus(204)
    
    def test_03_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
        
if __name__ == '__main__':
    import nose
    nose.runmodule()
