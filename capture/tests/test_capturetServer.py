import cherrypy
from cherrypy.test import helper
import uuid
import mimetypes
import os
import sys
import shutil
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import captureServer
from utils import io

DATA_DIR = os.path.abspath("data")
CONVENTIONAL_DIR = os.path.join(DATA_DIR, "conventional")

CONFIG = {
    "global": {
        "app_opts.general": {"testmode": True, "multiCapture": "simultaneousCapture", "delay": 10, "interval": 1}
    },
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
    "/data": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "data"
    }
}

def setup_server(config=CONFIG):
    captureServer.mountApp(config)
    
def teardown_server(dir=CONVENTIONAL_DIR):
    io.rmTree(dir)

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
            
class TestConfig(helper.CPWebCase):
    # hardcoding due to the fact that setup_server can't take any arguments, not even "self"
    def customServerSetup():
        setup_server({
            "global": {
                "server.socket_host": "0.0.0.0"
            }
        })
    
    setup_server = staticmethod(customServerSetup)
    teardown_server = staticmethod(teardown_server)
    
    def test_01_socket_host(self):
        self.assertEquals("0.0.0.0", cherrypy.config["server.socket_host"])

class TestRoot(ServerTestCase):
    rootURL = "/"
    expectedRedirectURL = "/components/cameras/html/cameras.html"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def test_01_get(self):
        self.getPage(self.rootURL)
        self.assertStatus(301)
        self.assertHeader("Location", cherrypy.url(self.expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.rootURL, ["PUT", "POST", "DELETE"])
        
    # Known failure since the rediction has NOT been implemented.
#    def test_03_redirectURL(self):
#        self.getPage(self.expectedRedirectURL)
#        self.assertStatus(200)

class TestCameras(ServerTestCase):
    camerasURL = "/cameras/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.camerasURL, ["PUT", "POST", "DELETE"])

    def test_02_get(self):
        self.getPage(self.camerasURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

class TestCapture(ServerTestCase):
    conventionalURL = "/conventional/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalURL, ["PUT", "POST", "DELETE"])

    def test_02_get(self):
        self.getPage(self.conventionalURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

class TestCamerasStatus(ServerTestCase):
    conventionalCamerasURL = "/conventional/cameras/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCamerasURL, ["PUT", "POST", "DELETE"])

    def test_02_get(self):
        self.getPage(self.conventionalCamerasURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

class TestCameraCapture(ServerTestCase):
    conventionalCaptureURL = "/conventional/capture/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCaptureURL, ["PUT"])

    def test_02_get(self):
        expectedFiles = []
        self.getPage(self.conventionalCaptureURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

    def test_03_post(self):
        headers = [
            ("Content-Length", 0),
            ("Content-Type", "text/plain"),
            ("Pragma", "no-cache"),
            ("Cache-Control", "no-cache")
        ]
        
        self.getPage(self.conventionalCaptureURL, headers, "POST", "")
        self.assertStatus(202)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

    def test_04_delete(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))
        self.getPage(self.conventionalCaptureURL, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should have been removed".format(CONVENTIONAL_DIR))
        
class CaptureImages(ServerTestCase):
    conventionalCaptureImagesURL = "/conventional/capture/images/"
    conventionalCaptureImagesIndexURL = conventionalCaptureImagesURL + "1/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCaptureImagesURL, ["GET", "DELETE", "POST", "PUT"])
        self.assertUnsupportedHTTPMethods(self.conventionalCaptureImagesIndexURL, ["POST", "PUT"])
        
    def test_02_get(self):
        expected = {"images": []}
        self.getPage(self.conventionalCaptureImagesIndexURL);
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(json.dumps(expected))
        
    def test_03_delete(self):
        self.getPage(self.conventionalCaptureImagesIndexURL, method="DELETE");
        self.assertStatus(204)

if __name__ == '__main__':
    import nose
    nose.runmodule()
