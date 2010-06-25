"""Module contains a mock Decapod server for testing purposes.

It always pretends there are two cameras connected and returns images from the
local filesystem instead of using gphoto.
"""

import resourcesource
import cherrypy
import glob
import os
import simplejson as json
import sys
from PIL import Image

imageIndex = 0

# Setup configuration for static resources within the server.
serverConfigPath = os.path.join(resourcesource.serverBasePath, "decapod-resource-config.json")
resources = resourcesource.ResourceSource(serverConfigPath)

# Create the captured images directory if needed.
if os.path.exists(resouces.filePath("${capturedImages}")) == False:
    os.mkdir(resouces.filePath("${capturedImages}"))
    
class ImageController(object):
    """Main class for manipulating images.

    Exposes operations such as capturing, post-processing and deleting pictures
    and sets of pictures. All URLs are considered a path to an image or to a set
    of images represented by a JSON file of their attributes."""

    images = []

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
            params = cherrypy.request.params
            ports, models = [None, None], [None, None]
            if "ports" in params and "models" in params:
                ports, models = params["ports"], params["models"]

            assert len(ports) >= 2
            assert len(models) >= 2

            firstImagePath  = self.take_picture()
            secondImagePath = self.take_picture()

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

    def take_picture(self, port=None, model=None):
        """Copies an image from the mock images folder to the captured images folder."""
        global imageIndex        
        
        capturedFileName = "Image%d.jpg" % (imageIndex)
        capturedFilePath = "${capturedImages}/" + capturedFileName
        imageIndex = imageIndex + 1
        
        files = glob.glob(resources.filePath("${mockImages}/*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(resources.filePath(capturedFilePath));
        
        return capturedFilePath

    def delete(self, index=None):
        """Delete an image from the list of images and from the file system."""

        for filename in self.images[index].values():
            os.unlink(filename)
        self.images.pop(index)
        return

    def generateThumbnail (self, fullSizeImagePath):
        size = 100, 146
        im = Image.open(resources.filePath(fullSizeImagePath))
        im.thumbnail(size, Image.ANTIALIAS)
        thumbnailPath = fullSizeImagePath[:-4] + "-thumb.jpg"
        im.save(resources.filePath(thumbnailPath))
        return thumbnailPath
    
    def stitchImages (self, firstImagePath, secondImagePath):
        # The stitched file should be named as a concatenation of the two image names.
        stitchFileName = resources.getFileName(firstImagePath)[0] \
                         + "-" + \
                         resources.getFileName(secondImagePath)[0] \
                         + ".png"
        
        # Save the stitched image in the same location as the first image.
        stitchFilePath = resources.getPathHead(firstImagePath) + stitchFileName
        os.system ("decapod-stitching -R rr %s %s -o %s" % (resources.filePath(firstImagePath), \
                                                            resources.filePath(secondImagePath), \
                                                            resources.filePath(stitchFilePath)))
        return stitchFilePath
        
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

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/capture")

    @cherrypy.expose
    def capture(self):
        # TODO: Hardcoded path. Remove it.
        html_path = resources.filePath("${components}/capture/html/Capture.html")
        file = open(html_path)
        content = file.read()
        file.close()
        return content

    @cherrypy.expose
    def cameras(self):
        """Pretends it detects two cameras locally attached to the PC.

        Returns a JSON document, describing the cameras and their capabilities:
        model, port, download support, and capture support."""

        cameras = [{"model": "Canon Powershot SX110IS", "port": "usb:002,012", "capture": True, "download": True},
                   {"model": "Nikon D80", "port": "usb:003,004", "capture": True, "download": True}]

        cherrypy.response.headers["Content-type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Cameras.json"
        return json.dumps(cameras)

if __name__ == "__main__":
    root = MockServer()
    root.images = ImageController()
    root.pdf = Export()
    cherrypy.quickstart(root, "/", resources.cherryPyConfig())
