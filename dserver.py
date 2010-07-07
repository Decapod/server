"""Module contains a fully operable stand-alone Decapod server.

It provides a resource-oriented approach to working with images (capturing,
deleting, generating thumbnails). It can be used with any client using the
provided uniform interface for accessing and modifying images.
"""

import cherrypy
import glob
import os
import simplejson as json
import sys
from PIL import Image

import resourcesource
import imageprocessing
import cameras

imageIndex = 0

# Setup configuration for static resources within the server.
serverConfigPath = os.path.join(resourcesource.serverBasePath, "decapod-resource-config.json")
resources = resourcesource.ResourceSource(serverConfigPath)

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
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename='CapturedImages.json'"
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
            stitchedPath = self.processor.stitch(firstImagePath, secondImagePath)
            model_entry["spread"] = resources.webURL(stitchedPath)
            thumbnailPath =self.processor.thumbnail(stitchedPath)
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
                try:
                    file = open(path)
                except IOError:
                    raise cherrypy.HTTPError(404, "Image path can not be opened")
                    
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

    def generateThumbnail (self, filepath):
        self.processor.thumbnail(filepath)

    def stitchImages (self, image_one, image_two):
        return self.processor.stitch(image_one, image_two)
        
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
            images = json.loads(cherrypy.request.params["images"])
            fileStr = ''
            for img in images:
                fileStr += '%s %s ' % (img['left'], img['right'])

            #TODO: make export asynchronous and abstracted from server.
            #TODO: change new filename FLUID-3538
            # hard coding the clean up of the pdf directory because a bug here can do some damage 
            # this will be removed post 0.3 when the implementation details of pdf generation are abstracted from CherryPY
            os.system("rm -rf pdf/tmpdir")
            os.system("rm pdf/*")
            status = os.system("mogrify -path %s -format tiff %s" % (exportPdfPath, fileStr))
            if status !=0:
                raise cherrypy.HTTPError(500, "Could not create path %s." % exportPdfPath)

            status = os.system("tiffcp %s/*.tiff %s/multi-page.tiff" % (exportPdfPath, exportPdfPath))
            if status !=0:
                raise cherrypy.HTTPError(500, "Could not generate tiff")

            status = os.system("decapod-genpdf.py -d %s/tmpdir -p %s/DecapodExport.pdf -b %s/multi-page.tiff -v 1" % (exportPdfPath, exportPdfPath, exportPdfPath)) 
            #TODO: give a better export PDF filename
            if status !=0:
                raise cherrypy.HTTPError(500, "Could not create PDF." )

            return exportPdfPath + "/DecapodExport.pdf" 
        else:
            cherrypy.response.headers["Allow"] = "GET, POST"
            raise cherrypy.HTTPError(405)

class DecapodServer(object):
    """Main class for the Decapod server.

    Exposes the index and capture pages as a starting point for working with the
    application. Does not expose any image-related functionality."""

    cameraSource = None

    def __init__(self):
        # TODO: Move this to IoC so we can get rid of Decapod/Mock server distinction altogether.
        self.cameraSource = cameras.Cameras(resources, \
                                            "${config}/decapod-supported-cameras.json")
                
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/capture")

    @cherrypy.expose
    def capture(self):
        # TODO: Chuck this.
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
