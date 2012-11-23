import cherrypy
from cherrypy.test import helper
import os
import sys
import re
import shutil
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
sys.path.append(os.path.abspath(os.path.join('..', '..', '..', 'decapod-dewarping')))
import dewarpProcessor
import dewarpServer
from utils import io, image
from serverTestCase import ServerTestCase

DATA_DIR = os.path.abspath("data")
MOCK_DATA_DIR = os.path.abspath("mockData")
CONVENTIONAL_DIR = os.path.join(DATA_DIR, "conventional")

CONFIG = {
    "/": {
        "tools.staticdir.root": os.getcwd(),
        "request.dispatch": cherrypy.dispatch.MethodDispatcher()
    },
    "/lib": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/lib"
    },
    "/dewarp": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": "../../../decapod-ui/dewarp"
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
    dewarpServer.mountApp(config)
    
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
    expectedRedirectURL = "/dewarp/html/dewarper.html"
    
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

class TestColourPicker(ServerTestCase):
    url = "/colourPicker/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
    
    def tearDown(self):
        io.rmTree(DATA_DIR)
    
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.url, ["POST", "GET", "DELETE"])

class TestDewarpArchive(ServerTestCase):
    url = "/dewarpedArchive/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
    
    def tearDown(self):
        io.rmTree(DATA_DIR)
    
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.url, ["POST"])
        
    def test_02_get(self):
        self.getPage(self.url)
        self.assertStatus(200)
        self.assertDictEqual({"status": dewarpProcessor.DEWARP_READY}, json.loads(self.body))
        
    def test_03_get_error(self):
        expected = {"status": dewarpProcessor.DEWARP_ERROR}
        io.writeToJSONFile(expected, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url)
        self.assertStatus(500)
        body = json.loads(self.body)
        self.assertEquals(dewarpProcessor.DEWARP_ERROR, body["status"])
        
    def test_04_get_complete(self):
        expected = {"status": dewarpProcessor.DEWARP_COMPLETE}
        io.writeToJSONFile(expected, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url)
        self.assertStatus(200)
        body = json.loads(self.body)
        self.assertEquals(dewarpProcessor.DEWARP_COMPLETE, body["status"])
        
        regexPattern = "http://127.0.0.1:\d*/data/captures-dewarped.zip"           
        regex = re.compile(regexPattern)
        self.assertTrue(regex.findall(body["url"]))
        
    def test_05_delete(self):
        self.getPage(self.url, method="DELETE")
        self.assertStatus(204)

    def test_06_delete_error(self):
        io.writeToJSONFile({"status": dewarpProcessor.DEWARP_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url, method="DELETE")
        self.assertStatus(409)

class TestCalibration(ServerTestCase):
    url = "/calibration/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
    
    def tearDown(self):
        io.rmTree(DATA_DIR)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.url, ["POST"])
        
    def tests_02_get(self):
        io.makeDirs(os.path.join(DATA_DIR, "calibration"))
        self.getPage(self.url)
        self.assertStatus(500)
        
    def tests_03_get_none(self):
        self.getPage(self.url)
        self.assertStatus(404)
        
    def tests_04_delete(self):
        calibrationDir = os.path.join(DATA_DIR, "calibration")
        io.makeDirs(calibrationDir)
        self.getPage(self.url, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(calibrationDir))
        
    def tests_05_delete_inProgress(self):
        calibrationDir = os.path.join(DATA_DIR, "calibration")
        io.makeDirs(calibrationDir)
        io.writeToJSONFile({"status": dewarpProcessor.DEWARP_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url, method="DELETE")
        self.assertStatus(409)
        self.assertInBody("Dewarping in progress, cannot delete until this process has finished")
        self.assertTrue(os.path.exists(calibrationDir))
        
    def tests_06_put_error(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"), method="PUT")
        self.assertStatus(500)
        
    def tests_07_put(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "valid_calibration.zip"), method="PUT")
        self.assertStatus(200)
        
    def tests_08_put_inProgress(self):
        io.writeToJSONFile({"status": dewarpProcessor.DEWARP_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"), method="PUT")
        self.assertStatus(409)
        self.assertInBody("Dewarping currently in progress, cannot accept another zip until this process has finished")
        
    def tests_09_put_badZip(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), method="PUT")
        self.assertStatus(500)

class TestCaptures(ServerTestCase):
    url = "/captures/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
    
    def tearDown(self):
        io.rmTree(DATA_DIR)
        
    def test_01_unsupportedMethods(self):
        self.assertUnsupportedHTTPMethods(self.url, ["POST"])
        
    def tests_02_get(self):
        io.makeDirs(os.path.join(DATA_DIR, "unpacked"))
        self.getPage(self.url)
        self.assertStatus(200)
        self.assertDictEqual({"numOfCaptures": 0}, json.loads(self.body))
        
    def tests_03_get_none(self):
        self.getPage(self.url)
        self.assertStatus(404)
        
    def tests_04_delete(self):
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        io.makeDirs(unpackedDir)
        self.getPage(self.url, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(unpackedDir))
        
    def tests_05_delete_inProgress(self):
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        io.makeDirs(unpackedDir)
        io.writeToJSONFile({"status": dewarpProcessor.DEWARP_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url, method="DELETE")
        self.assertStatus(409)
        self.assertInBody("Dewarping in progress, cannot delete until this process has finished")
        self.assertTrue(os.path.exists(unpackedDir))
        
    def tests_06_put(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"), method="PUT")
        self.assertStatus(200)
        self.assertDictEqual({"numOfCaptures": 0}, json.loads(self.body))
        
    def tests_07_put_inProgress(self):
        io.writeToJSONFile({"status": dewarpProcessor.DEWARP_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"), method="PUT")
        self.assertStatus(409)
        self.assertInBody("Dewarping currently in progress, cannot accept another zip until this process has finished")
        
    def tests_08_put_badZip(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"), method="PUT")
        self.assertStatus(500)

if __name__ == '__main__':
    import nose
    nose.runmodule()
