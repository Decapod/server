import cherrypy
from cherrypy.test import helper
import os
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import exportServer
from utils import io
from serverTestCase import ServerTestCase

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
        "tools.staticdir.dir": "../../../decapod-ui/lib"
    },
    "/components": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/components"
    },
    "/shared": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/shared"
    },
    "/library": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": LIBRARY_DIR
    }
}

def setup_server(config=CONFIG):
    exportServer.mountApp(config)
    
def teardown_server(dir=BOOK_DIR):
    io.rmTree(dir)
        
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
        io.makeDirs(BOOK_DIR)
    
    def tearDown(self):
        io.rmTree(BOOK_DIR)
     
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
class TestPDFExportExisting(ServerTestCase):
    exportURL = "/library/bookName/export/pdf/type1"
    exportStatus = '{"status": "complete", "url": "/library/book/export/pdf/Decapod.pdf"}'
    pdfDir = os.path.join(BOOK_DIR, "export", "pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    pdf = os.path.join(pdfDir, "Decapod.pdf")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        pdfSRC = os.path.abspath("data/pdf/Decapod.pdf")
        io.makeDirs(self.pdfDir)
        io.makeDirs(self.pdf)
        io.writeToFile(self.exportStatus, self.statusFile)
            
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
            
class TestPDFExportInProgress(ServerTestCase):
    exportURL = "/library/bookName/export/pdf/type1"
    exportStatus = '{"status": "in progress", "stage": ""}'
    pdfDir = os.path.join(BOOK_DIR, "export", "pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(self.pdfDir)
        io.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    def test_02_delete(self):
        self.getPage(self.exportURL, method="DELETE")
        self.assertStatus(409)
    
    def test_03_put(self):
        self.getPage(self.exportURL, method="PUT")
        self.assertStatus(202)
    
    def test_04_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
        
# TODO: Test put method, the trouble is that it is asynchronous       
class TestPDFExportNew(ServerTestCase):
    exportURLBase = "/library/bookName/export/pdf"
    exportURLType = os.path.join(exportURLBase, "type1")
    invalidTypeURL = os.path.join(exportURLBase, "2")
    exportStatus = '{"status": "ready"}'
    pdfDir = os.path.join(BOOK_DIR, "export", "pdf")
    statusFile = os.path.join(pdfDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(self.pdfDir)
        io.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURLType)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
     
    def test_02_delete(self):
        self.getPage(self.exportURLType, method="DELETE")
        self.assertStatus(204)
    
    def test_03_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURLType, ["POST"])
        
    def test_04_put_invalidType(self):
        self.getPage(self.invalidTypeURL, method="PUT")
        self.assertStatus(400)
        
    def test_05_put_missingType(self):
        self.getPage(self.exportURLBase, method="PUT")
        self.assertStatus(405)
        
# TODO: Test put method, the trouble is that it is asynchronous       
class TestImageExportExisting(ServerTestCase):
    exportURL = "/library/bookName/export/image/tiff"
    exportStatus = '{"status": "complete", "url": "/library/book/export/image/Decapod.zip"}'
    imgDir = os.path.join(BOOK_DIR, "export", "image")
    statusFile = os.path.join(imgDir, "exportStatus.json")
    archive = os.path.join(imgDir, "Decapod.zip")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(self.imgDir)
        shutil.copy(os.path.join(DATA_DIR, "pdf", "Decapod.pdf"), self.archive) #just need a dummy file, renaming the pdf to act as the zip
        io.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    def test_02_delete(self):
        self.assertTrue(os.path.exists(self.archive), "The Decapod.zip file should exist at path ({0})".format(self.archive))
        self.getPage(self.exportURL, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(self.archive), "The Decapod.zip file should no longer exist at path ({0})".format(self.archive))
    
    def test_03_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
            
class TestImageExportInProgress(ServerTestCase):
    exportURL = "/library/bookName/export/image/tiff"
    exportStatus = '{"status": "in progress"}'
    imgDir = os.path.join(BOOK_DIR, "export", "image")
    statusFile = os.path.join(imgDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(self.imgDir)
        io.writeToFile(self.exportStatus, self.statusFile)
            
    def test_01_get(self):
        self.getPage(self.exportURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(self.exportStatus)
    
    def test_02_delete(self):
        self.getPage(self.exportURL, method="DELETE")
        self.assertStatus(409)
    
    def test_03_put(self):
        self.getPage(self.exportURL, method="PUT")
        self.assertStatus(202)
    
    def test_04_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.exportURL, ["POST"])
        
# TODO: Test put method, the trouble is that it is asynchronous       
class TestImageExportNew(ServerTestCase):
    exportURLBase = "/library/bookName/export/image"
    exportURL = os.path.join(exportURLBase, "tiff")
    exportStatus = '{"status": "ready"}'
    imgDir = os.path.join(BOOK_DIR, "export", "image")
    statusFile = os.path.join(imgDir, "exportStatus.json")
    
    setup_server = staticmethod(setup_server)
    tearDown = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(self.imgDir)
        io.writeToFile(self.exportStatus, self.statusFile)
            
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
        
    def test_04_put_missingFormat(self):
        self.getPage(self.exportURLBase, method="PUT")
        self.assertStatus(405)
         
if __name__ == '__main__':
    import nose
    nose.runmodule()
