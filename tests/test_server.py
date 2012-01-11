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

CAPTURED_IMAGES_ROOT = "/book/capturedImages/"

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
    
    def takePicture(self):
        postBody = ""
        self.getPage("/images/", method="POST", body=postBody, headers=self.jsonHeader)
        return postBody
    
    def checkPageSpread(self, pageSpread, firstImageName, secondImageName):
        # Test the left and right image URLs.
        self.assertEqual(pageSpread["left"], CAPTURED_IMAGES_ROOT + firstImageName + ".jpg", \
                         "The URL for the first image should be relative to the capturedImages resource. Actual is: " \
                         + pageSpread["left"])
        self.assertEqual(pageSpread["right"], CAPTURED_IMAGES_ROOT + secondImageName + ".jpg", \
                         "The URL for the second image should be relative to the capturedImages resource. Actual is: " \
                         + pageSpread["right"])
        
        # Check the spread image and thumbnail URLs. They should be:
        #   * Relative to the /testData resource
        #   * a concatenation of the first and second image names
        #   * thumbnails should have -thumb suffix
        spreadImageName = firstImageName + "-mid" + "-" + secondImageName + "-mid"
        self.assertEqual(pageSpread["spread"], CAPTURED_IMAGES_ROOT + spreadImageName + ".png", \
                        "The URL for spread image should be relative to the capturedImages resource. Actual value is: " \
                        + pageSpread["spread"])
         
        self.assertEqual(pageSpread["thumb"], CAPTURED_IMAGES_ROOT + spreadImageName + "-thumb.png", \
                         "The URL for spread thumbnail should be relative to the capturedImages resource. Actual value is:" \
                         + pageSpread["thumb"])
    
    def test_00_getRoot(self):
        """ 
        Ensures that / redirects to the book management page
        """
        
        expectedRedirectURL = "/components/bookManagement/html/bookManagement.html"
        
        #tests the request for the capture page
        self.getPage("/")
        self.assertStatus(303)
        self.assertHeader('Location', cherrypy.url(expectedRedirectURL))
        
        self.getPage(expectedRedirectURL)
        self.assertStatus(200)
        
    def test_01_getCameras(self):
        """
        Tests the GET request for retrieving the camera info
        """
        #tests the GET request for retrieving the camera info
        self.getPage("/cameras/")
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
        self.takePicture()
        self.assertStatus(200)
        result = self.assertJSON(4)
        self.checkPageSpread(result, "decapod-0001", "decapod-0002")
        
    # NOTE: This test is quite slow (due to genpdf being slow), so run it before capturing a lot of images.
    def test_04_postPDF(self):
        """
        Tests the POST request for generating a PDF
        """
        postBody = ""
        self.getPage("/pdf", method="POST", body=postBody, headers=[("Accept", "*/*")])
        self.assertStatus(200)
        self.assertHeader('Content-Type', 'text/html')
        self.assertEqual(self.body, "/book/pdf/Decapod.pdf")
        
    def test_05_getImages_after_capture(self):
        self.takePicture()
        self.getPage("/images/")
        self.assertStatus(200)
        result = self.assertJSON(2)
        self.checkPageSpread(result[0], "decapod-0001", "decapod-0002")
        self.checkPageSpread(result[1], "decapod-0003", "decapod-0004")        
    