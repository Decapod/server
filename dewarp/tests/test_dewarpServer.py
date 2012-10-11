import cherrypy
from cherrypy.test import helper
import os
import sys
import re
import shutil
import uuid
import mimetypes
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import dewarpProcessor
import dewarpServer
from utils import io, image

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
    dewarpServer.mountApp(config)
    
def teardown_server(dir=CONVENTIONAL_DIR):
    io.rmTree(dir)
    sys.exit()

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
    
    def fileUploadParams(self, path):
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
        Uploads the file at 'path' to the resource at 'url'
        '''
        headers, body = self.fileUploadParams(path)
        self.getPage(url, headers, "PUT", body)
            
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
    expectedRedirectURL = "/components/dewarp/html/dewarp.html"
    
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
        
    def test_02__get(self):
        self.getPage(self.url)
        self.assertStatus(200)
        self.assertDictEqual({"status": dewarpProcessor.EXPORT_READY}, json.loads(self.body))
        
    def test_03__get_complete(self):
        expected = {"status": dewarpProcessor.EXPORT_COMPLETE}
        io.writeToJSONFile(expected, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url)
        self.assertStatus(200)
        body = json.loads(self.body)
        self.assertEquals(dewarpProcessor.EXPORT_COMPLETE, body["status"])
        
        regexPattern = "http://127.0.0.1:\d*/data/export.zip"           
        regex = re.compile(regexPattern)
        self.assertTrue(regex.findall(body["url"]))
        
    def test_04_delete(self):
        self.getPage(self.url, method="DELETE")
        self.assertStatus(204)

    def test_05_delete_error(self):
        io.writeToJSONFile({"status": dewarpProcessor.EXPORT_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url, method="DELETE")
        self.assertStatus(409)

class TestCaptures(ServerTestCase):
    url = "/captures/"
    
    setup_server = staticmethod(setup_server)
    teardown_server = staticmethod(teardown_server)
    
    def setUp(self):
        io.makeDirs(DATA_DIR)
    
    def tearDown(self):
        io.rmTree(DATA_DIR)
        
    def tests_02_get(self):
        io.makeDirs(os.path.join(DATA_DIR, "unpacked", "calibration"))
        self.getPage(self.url)
        self.assertStatus(200)
        self.assertDictEqual({"numOfCaptures": 0}, json.loads(self.body))
        
    def tests_03_get_none(self):
        self.getPage(self.url)
        self.assertStatus(404)
        
    def tests_04_get_noCalibration(self):
        io.makeDirs(os.path.join(DATA_DIR, "unpacked"))
        self.getPage(self.url)
        self.assertStatus(500)
        self.assertDictEqual({"ERROR_CODE": "CalibrationDirNotExist", "msg": "The calibration directory \"{0}\" does not exist.".format(os.path.join(DATA_DIR, "unpacked", "calibration"))}, json.loads(self.body))
        
    def tests_05_delete(self):
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        calibrationDir = os.path.join(unpackedDir, "calibration")
        io.makeDirs(calibrationDir)
        self.getPage(self.url, method="DELETE")
        self.assertStatus(204)
        self.assertFalse(os.path.exists(unpackedDir))
        self.assertFalse(os.path.exists(calibrationDir))
        
    def tests_06_delete_inProgress(self):
        unpackedDir = os.path.join(DATA_DIR, "unpacked")
        calibrationDir = os.path.join(unpackedDir, "calibration")
        io.makeDirs(calibrationDir)
        io.writeToJSONFile({"status": dewarpProcessor.EXPORT_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.getPage(self.url, method="DELETE")
        self.assertStatus(409)
        self.assertInBody("Dewarping in progress, cannot delete until this process has finished")
        self.assertTrue(os.path.exists(unpackedDir))
        self.assertTrue(os.path.exists(calibrationDir))
        
    def tests_07_put(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"))
        self.assertStatus(200)
        self.assertDictEqual({"numOfCaptures": 0}, json.loads(self.body))
        
    def tests_08_put_inProgress(self):
        io.writeToJSONFile({"status": dewarpProcessor.EXPORT_IN_PROGRESS}, os.path.join(DATA_DIR, "status.json"));
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "empty_captures.zip"))
        self.assertStatus(409)
        self.assertInBody("Dewarping currently in progress, cannot accept another zip until this process has finished")
        
    def tests_09_put_badZip(self):
        self.uploadFile(self.url, os.path.join(MOCK_DATA_DIR, "capture-0_1.jpg"))
        self.assertStatus(500)

if __name__ == '__main__':
    import nose
    nose.runmodule()
