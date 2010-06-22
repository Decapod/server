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
resources = resourcesource.ResourceSource("decapod-resource-config.json")

 #TODO: change to a better path FLUID-3538
mockImagesPath = resources.filePath("mockImages")
capturedImagesPath = resources.filePath("capturedImages")

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

            # TODO: This is all lame. Move it all into the ResourceSource
            # and express as "virtual relative paths" (e.g. ${capturedImages}/firstImageFileName)
            
            firstImageFileName  = self.take_picture()
            firstImageURL = resources.webURL("capturedImages") + "/" + firstImageFileName
            firstImagePath = os.path.join(resources.filePath("capturedImages"), firstImageFileName)
            
            secondImageFileName = self.take_picture()
            secondImageURL = resources.webURL("capturedImages") + "/" + secondImageFileName
            secondImagePath = os.path.join(resources.filePath("capturedImages"), secondImageFileName)

            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % len(self.images)
            model_entry = {"left": firstImageURL, "right": secondImageURL}

            #TODO: add page order correction.            

            stitchedFileName = self.stitchImages(firstImagePath, secondImagePath)
            model_entry["spread"] = resources.webURL("capturedImages") + "/" + stitchedFileName
            spreadPath = os.path.join(resources.filePath("capturedImages"), stitchedFileName)
            model_entry["thumb"]  = resources.webURL("capturedImages") + "/" + self.generateThumbnail(spreadPath)

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
        capturedFilePath = os.path.join(capturedImagesPath, capturedFileName)  
        imageIndex = imageIndex + 1
        
        files = glob.glob(os.path.join(mockImagesPath, "*"))
        files.sort()
        file_count = len(files)

        name_to_open = files[imageIndex % file_count]
        im = Image.open(name_to_open)
        im.save(capturedFilePath);
        
        return capturedFileName

    def delete(self, index=None):
        """Delete an image from the list of images and from the file system."""

        for filename in self.images[index].values():
            os.unlink(filename)
        self.images.pop(index)
        return

    def generateThumbnail (self, filepath):
        size = 100, 146
        im = Image.open(filepath)
        im.thumbnail(size, Image.ANTIALIAS)
        # TODO: idiotic
        thumbnailFileName = filepath.split('/').pop()[:-4] + "-thumb.jpg" 
        thumbnailPath = filepath[:-4] + "-thumb.jpg"
        im.save(thumbnailPath)
        return thumbnailFileName

    def stitchImages (self, image_one, image_two):
        # TODO: This is idiotic
        stitchFileName = image_one.split('/').pop()
        stitchFileName = stitchFileName[:-4] + "-" +image_two.split('/').pop()
        stitchFileName = stitchFileName[:-4] + ".png"
        
        stitchFilePath = os.path.join(capturedImagesPath, stitchFileName)

        #Image Magick implementation
        #os.system ("convert %s %s +append %s" % (image_one, image_two, stitchFilepath))

        #Decapod implementation
        os.system ("decapod-stitching -R rr %s %s -o %s" % (image_one, image_two, stitchFilePath))

        return stitchFileName
        
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
        html_path = os.path.join(resourcesource.serverBasePath, \
                                 "../decapod-ui/components/capture/html/Capture.html")
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
