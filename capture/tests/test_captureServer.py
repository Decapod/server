import cherrypy
from cherrypy.test import helper
import os
import sys
import re
import shutil
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import captureServer
from utils import io, image
from serverTestCase import ServerTestCase

DATA_DIR = os.path.abspath("data")
MOCK_DATA_DIR = os.path.abspath("mockData")
CONVENTIONAL_DIR = os.path.join(DATA_DIR, "conventional")
CAPTURES_DIR = os.path.join(CONVENTIONAL_DIR, "captures")

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
    "/capture": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/capture"
    },
    "/core": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/core"
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
    sys.exit()
            
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
    expectedRedirectURL = "/capture/html/capture.html"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def test_01_get(self):
        self.getPage(self.rootURL)
        self.assertStatus(301)
        self.assertHeader("Location", cherrypy.url(self.expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.rootURL, ["PUT", "POST", "DELETE"])
        
    def test_03_redirectURL(self):
        self.getPage(self.expectedRedirectURL)
        self.assertStatus(200)

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

class TestTypeCamerasStatus(ServerTestCase):
    conventionalCamerasURL = "/conventional/cameras/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCamerasURL, ["PUT", "POST", "DELETE"])

    def test_02_get(self):
        self.getPage(self.conventionalCamerasURL)
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

class TestTypeCameraCapture(ServerTestCase):
    conventionalCaptureURL = "/conventional/capture/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def tearDown(self):
        io.rmFile(os.path.join(CONVENTIONAL_DIR, "captureStatus.json"))
        
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
        
        expectedCaptures = None
        
        self.getPage(self.conventionalCaptureURL, headers, "POST", "")
        self.assertStatus(202)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        
        regexPattern ='{"captures": \["http://127.0.0.1:\d*/data/conventional/captures/capture-1_0.jpeg", "http://127.0.0.1:\d*/data/conventional/captures/capture-1_1.jpeg"\], "totalCaptures": 1, "captureIndex": 1}'            
        regex = re.compile(regexPattern)
        self.assertTrue(regex.findall(self.body))
        
    def test_04_delete(self):
        self.assertTrue(os.path.exists(CONVENTIONAL_DIR), "The 'conventional' directory (at path: {0}) should currently exist".format(CONVENTIONAL_DIR))
        self.getPage(self.conventionalCaptureURL, method="DELETE")
        self.assertStatus(204)
        self.assertListEqual(["captureStatus.json"], os.listdir(CONVENTIONAL_DIR))
        
class CaptureImages(ServerTestCase):
    conventionalCaptureImagesURL = "/conventional/capture/images/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCaptureImagesURL, ["GET", "POST", "PUT"])
        
    def test_03_delete(self):
        self.getPage(self.conventionalCaptureImagesURL, method="DELETE");
        self.assertStatus(204)

class ImageIndex(ServerTestCase):
    conventionalCaptureImagesIndexURL = "/conventional/capture/images/0/"
    conventionalCaptureImagesFirstURL = "/conventional/capture/images/first/"
    conventionalCaptureImagesLastURL = "/conventional/capture/images/last/"
    conventionalCaptureImagesErrorURL = "/conventional/capture/images/error/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(CAPTURES_DIR)
        
    def tearDown(self):
        io.rmTree(CAPTURES_DIR)
    
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.conventionalCaptureImagesIndexURL, ["POST", "PUT"])
        
    def test_02_get_none(self):
        expected = {"images": []}
        self.getPage(self.conventionalCaptureImagesIndexURL);
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")
        self.assertBody(json.dumps(expected))
        
    def test_02_get(self):
        imgDir = os.path.join(MOCK_DATA_DIR, "images")
        images = image.findImages(imgDir)
        for one_image in images:
            shutil.copy(one_image, CAPTURES_DIR)
            
        self.getPage(self.conventionalCaptureImagesIndexURL);
        self.assertStatus(200)
        self.assertHeader("Content-Type", "application/json", "Should return json content")

        regexPattern = '{"images": \["http://127.0.0.1:\d*/data/conventional/captures/capture-0_2.jpg", "http://127.0.0.1:\d*/data/conventional/captures/capture-0_1.jpg"\]}'
            
        regex = re.compile(regexPattern)
        self.assertTrue(regex.findall(self.body))
        
        io.rmTree(CONVENTIONAL_DIR)
        
    def test_03_get_error(self):
        self.getPage(self.conventionalCaptureImagesErrorURL)
        self.assertStatus(404)
        
    def test_04_delete(self):
        self.getPage(self.conventionalCaptureImagesIndexURL, method="DELETE");
        self.assertStatus(204)

if __name__ == '__main__':
    import nose
    nose.runmodule()
