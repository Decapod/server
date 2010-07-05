"""Module contains a mock Decapod server for testing purposes.

It always pretends there are two cameras connected and returns images from the
local filesystem instead of using gphoto.
"""

import cherrypy
import os
import simplejson as json
import sys

import resourcesource
import imageprocessing
import cameras

# Setup configuration for static resources within the server.
serverConfigPath = os.path.join(resourcesource.serverBasePath, "decapod-resource-config.json")
resources = resourcesource.ResourceSource(serverConfigPath)

# Create the captured images directory if needed.
if os.path.exists(resources.filePath("${capturedImages}")) == False:
    os.mkdir(resources.filePath("${capturedImages}"))
    
class ImageController(object):
    """Main class for manipulating images.

    Exposes operations such as capturing, post-processing and deleting pictures
    and sets of pictures. All URLs are considered a path to an image or to a set
    of images represented by a JSON file of their attributes."""

    images = []
    processor = imageprocessing.ImageProcessor(resources)
    cameraSource = None
    
    def __init__(self, cameras):
        self.cameraSource = cameras
        
    @cherrypy.expose
    def index(self, *args, **kwargs):
        """Handles the /images/ URL - a collection of sets of images.

        Supports getting the list of images (GET) and adding a new image to the
        collection (POST). An option telling whether to use a camera can be
        passed. Also supports changing the list of images (PUT)"""
        print(self.images)
        method = cherrypy.request.method.upper()
        if method == "GET":
            cherrypy.response.headers["Content-Type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename='Captured images.json'"
            return json.dumps(self.images)

        elif method == "POST":
            firstImagePath, secondImagePath = self.cameraSource.captureImagePair()
            
            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % len(self.images)
            model_entry = {
                "left": resources.webURL(firstImagePath), 
                "right": resources.webURL(secondImagePath)
            }

            #TODO: add page order correction.            
            stitchedPath = self.stitchImages(firstImagePath, secondImagePath)
            model_entry["spread"] = resources.webURL(stitchedPath)
            thumbnailPath = self.generateThumbnail(stitchedPath)
            model_entry["thumb"]  = resources.webURL(thumbnailPath)

            self.images.append(model_entry)
            return json.dumps(model_entry)

        elif method == "PUT":
            params = cherrypy.request.params
            self.images = json.loads(params["images"])
            return params["images"]

        else:
            cherrypy.response.headers["Allow"] = "GET, POST, PUT"
            raise cherrypy.HTTPError(405)

    @cherrypy.expose
    def default(self, id, state=None):
        """Handles the /images/:id/ and /images/:id/:state URLs.

        Supports getting (GET) and deleting (DELETE) sets of images by their id.
        The first operation returns a JSON text with the paths to the images. If
        state is provided, GET returns a jpeg image with the specified state.
        POST is supported together with state, performing some operation(s) on
        the image."""

        index = int(id)
        if index < 0 or index >= len(self.images):
            raise cherrypy.HTTPError(404, "The specified resource is not currently available.")

        method = cherrypy.request.method.upper()
        if not state:
            if method == "GET":
                cherrypy.response.headers["Content-Type"] = "application/json"
                cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % index
                return json.dumps(self.images[index])

            elif method == "DELETE":
                return self.delete(index)

            else:
                cherrypy.response.headers["Allow"] = "GET, DELETE"
                raise cherrypy.HTTPError(405)

        else:
            if method == "GET":
                if not state in self.images[index]:
                    raise cherrypy.HTTPError(404, "The specified resource is not currently available.")

                path = self.images[index][state]
                cherrypy.response.headers["Content-type"] = "image/jpeg"
                file = open(path)
                content = file.read()
                file.close()
                return content

            else:
                cherrypy.response.headers["Allow"] = "GET"
                raise cherrypy.HTTPError(405)

    def delete(self, index=None):
        """Delete an image from the list of images and from the file system."""

        for filename in self.images[index].values():
            os.unlink(filename)
        self.images.pop(index)
        return

    def generateThumbnail (self, fullSizeImagePath):
        return self.processor.thumbnail(fullSizeImagePath)
    
    def stitchImages (self, firstImagePath, secondImagePath):
        return self.processor.stitch(firstImagePath, secondImagePath)
        
class Export(object):

    @cherrypy.expose
    def default(self, name=None, images=[]):
        exportPdfPath = "pdf"

        # Check save path for images.
        # TODO: move this to server initialization so it's only done once (FLUID-3537)
        if not os.access (exportPdfPath,os.F_OK) and os.access ("./",os.W_OK):
            status = os.system("mkdir %s" % exportPdfPath)
            if status !=0:
                raise cherrypy.HTTPError(403, "Could not create path %s." % exportPdfPath)
        elif not os.access ("./",os.W_OK):
            raise cherrypy.HTTPError(403, "Can not write to directory")


        method = cherrypy.request.method.upper()
        if method == "GET":
            file = open(exportPdfPath + name)
            content = file.read()
            file.close()
            return content
        elif method == "POST":
            # The mockserver does not actually generate the pdf

            return exportPdfPath + "/DecapodExport.pdf" 
        else:
            cherrypy.response.headers["Allow"] = "GET, POST"
            raise cherrypy.HTTPError(405)

class MockServer(object):
    """Main class for the mock server.

    Exposes the index and capture pages as a starting point for working with the
    application. Does not expose any image-related functionality."""

    cameraSource = None

    def __init__(self):
        supportedCamerasJSON = open(resources.filePath("${config}/decapod-supported-cameras.json"))
        supportedCameras = json.load(supportedCamerasJSON)
        self.cameraSource = cameras.MockCameras(supportedCameras, resources)
        
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/capture")

    @cherrypy.expose
    def capture(self):
        # TODO: Chuck this
        html_path = resources.filePath("${components}/capture/html/Capture.html")
        file = open(html_path)
        content = file.read()
        file.close()
        return content

    @cherrypy.expose
    def cameras(self):
        cameraStatus = self.cameraSource.cameraInfo()
        cherrypy.response.headers["Content-type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Cameras.json"
        return json.dumps(cameraStatus)
