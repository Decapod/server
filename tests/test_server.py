import httplib
import os.path
import urllib
import cherrypy
import simplejson
import sys
from cherrypy.test import helper
import testutils
sys.path.append(os.path.abspath('..'))
import decapod


def initWithoutCameras():
    return decapod.mountApp("cameras.MockCameras")
    
def initWithRealCameras():
    return decapod.mountApp("cameras.Cameras")

# must be called setup_server
def setup_server():
    if len(sys.argv) > 1 and sys.argv[1] == "--use-cameras":
        initWithRealCameras()
    else:
        initWithoutCameras()

class TestRequests(helper.CPWebCase):
    
    jsonHeader = [("Accept", "application/json")]
    
    def tearDown(self):
        testutils.cleanUpCapturedImages()
    
    def assertJSON(self, numKeys=None):
        """ 
        A convenience function for testing the json data returned from a request. 
        Currently only tests that the Content-Type is 'application/json' and the 
        length matches the numKeys argument 
        """
        
        self.assertHeader("Content-Type", "application/json")
        json = simplejson.loads(self.body)
        if not numKeys == None:
            self.assertEqual(len(json), numKeys)
        return json
    
    def test_00_getCapture(self):
        """ 
        Ensures that the /capture page is mounted correctly and that / redirects
        to /capture
        """
        
        captureMount = "/capture"
        
        #tests the request for the capture page
        self.getPage("/")
        self.assertStatus(303)
        self.assertHeader('Location', cherrypy.url(captureMount))
        
        #throws a 500 error because the capture.html page isn't available.
        #will need the ui code here as well for this to work
        self.getPage(captureMount)
        self.assertStatus(200)

        
    def test_01_getCameras(self):
        """
        Tests the GET request for retrieving the camera info
        """
        #tests the GET request for retrieving the camera info
        self.getPage("/cameras")
        self.assertStatus(200)
        self.assertJSON(2)
        
    def test_02_getInitialImages_empty(self):
        """
        Tests the GET request for retrieving the images.
        Since this tests the initial state, the result should indicate that
        no images were present.
        """
        self.getPage("/images/")
        self.assertStatus(200)
        self.assertJSON(0)
    
    def test_03_takeImagesPOST(self):
        """
        Tests the POST request for taking a new image.
        """
        postBody = ""
        self.getPage("/images/", method="POST", body=postBody, headers=self.jsonHeader)
        self.assertStatus(200)
        result = self.assertJSON(4)
        
        firstImageName = "decapod-0001"
        secondImageName = "decapod-0002"
        
        # Test the left and right image URLs.
        self.assertEqual(result["left"], "/capturedImages/" + firstImageName + ".jpg", \
                         "The URL for the first image should be relative to the capturedImages resource. Actual is: " \
                         + result["left"])
        self.assertEqual(result["right"], "/capturedImages/" + secondImageName + ".jpg", \
                         "The URL for the second image should be relative to the capturedImages resource. Actual is: " \
                         + result["right"])
        
        # Check the spread image and thumbnail URLs. They should be:
        #   * Relative to the /testData resource
        #   * a concatenation of the first and second image names
        #   * thumbnails should have -thumb suffix
        spreadImageName = "/capturedImages/" + firstImageName + "-" + secondImageName
        self.assertEqual(result["spread"], spreadImageName + ".png", \
                        "The URL for spread image should be relative to the capturedImages resource. Actual value is: " \
                        + result["spread"])
         
        self.assertEqual(result["thumb"], spreadImageName + "-thumb.jpg", \
                         "The URL for spread thumbnail should be relative to the capturedImages resource. Actual value is:" \
                         + result["thumb"])
        

    
    def test_04_postPDF(self):
        """
        Tests the POST request for generating a PDF
        """
        postBody = ""
        self.getPage("/pdf", method="POST", body=postBody, headers=[("Accept", "*/*")])
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'text/html')
        self.assertEqual(self.body, "/generatedPDF/Decapod.pdf")
	