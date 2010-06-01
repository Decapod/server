import httplib
import os.path
import urllib
import cherrypy
import simplejson
import sys
sys.path.append(os.path.abspath('..'))
import mockserver
import servertest as stest

current_dir = os.path.abspath(os.path.dirname(__file__))

def setup_server():
    stest.setup_mockserver()

class TestRequests(stest.ServerTest):
    jsonHeader = [("Accept", "application/json")]
    
    def assertJSON(self, length=None):
        self.assertHeader("Content-Type", "application/json")
        json = simplejson.loads(self.body)
        if not length == None:
            self.assertEqual(len(json), length)
        return json
    
    def test_00_getCapture(self):
        #tests the request for the capture page
        self.getPage("/")
        self.assertStatus(303)
        
        #throws a 500 error because the capture.html page isn't available.
        #will need the ui code here as well for this to work
        result = self.getPage("/capture")
        self.assertStatus(200)

        
    def test_01_getCameras(self):
        #tests the GET request for retrieving the camera info
        self.getPage("/cameras")
        self.assertStatus(200)
        self.assertJSON(2)
        
    def test_02_getImages_empty(self):
        self.getPage("/images/")
        self.assertStatus(200)
        self.assertJSON(0)
    
    def test_03_postImages(self):
        #tests the POST request for adding images
        postBody = ""
        self.getPage("/images/", method="POST", body=postBody, headers=self.jsonHeader)
        self.assertStatus(200)
        json = self.assertJSON(4)
        self.failUnless(json["spread"])
        self.failUnless(json["thumb"])
        self.failUnless(json["left"])
        self.failUnless(json["right"])
    
    def test_04_postPDF(self):
        #tests the POST request for generating a PDF
        postBody = ""
        self.getPage("/pdf", method="POST", body=postBody, headers=[("Accept", "*/*")])
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'text/html')
        self.assertEqual(self.body, "pdf/DecapodExport.pdf")
	