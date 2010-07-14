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
import pdf

# Setup configuration for static resources within the server.
serverConfigPath = os.path.join(resourcesource.serverBasePath, "decapod-resource-config.json")
resources = resourcesource.ResourceSource(serverConfigPath)

class ImageController(object):
    """Main class for manipulating images.

    Exposes operations such as capturing, post-processing and deleting pictures
    and sets of pictures. All URLs are considered a path to an image or to a set
    of images represented by a JSON file of their attributes."""

    processor = imageprocessing.ImageProcessor(resources)
    cameraSource = None
    book = None
    
    def __init__(self, cameras, book):
        self.cameraSource = cameras
        self.book = book
        
    def createPageModelForWeb(self, bookPage):
        webModel = {}
        for image in bookPage.keys():
            webModel[image] = resources.webURL(bookPage[image])
            
        return json.dumps(webModel)
    
    @cherrypy.expose
    def index(self, *args, **kwargs):
        """Handles the /images/ URL - a collection of sets of images.

        Supports getting the list of images (GET) and adding a new image to the
        collection (POST). An option telling whether to use a camera can be
        passed. Also supports changing the list of images (PUT)"""

        method = cherrypy.request.method.upper()
        if method == "GET":
            cherrypy.response.headers["Content-Type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename='CapturedImages.json'"
            return json.dumps(self.book)

        elif method == "POST":
            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % len(self.book)
   
            #TODO: add page order correction.
            firstImagePath, secondImagePath = self.cameraSource.captureImagePair()
            stitchedPath = self.processor.stitch(firstImagePath, secondImagePath)
            thumbnailPath =self.processor.thumbnail(stitchedPath)

            page = {
                "left": firstImagePath,
                "right": secondImagePath,
                "spread": stitchedPath,
                "thumb": thumbnailPath
            }
            self.book.append(page)
                     
            return self.createPageModelForWeb(page)

        elif method == "PUT":
            # TODO: This method looks fatal. Do we really want it?
            params = cherrypy.request.params
            self.book = json.loads(params["images"])
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
        if index < 0 or index >= len(self.book):
            raise cherrypy.HTTPError(404, "The specified resource is not currently available.")

        method = cherrypy.request.method.upper()
        if not state:
            if method == "GET":
                cherrypy.response.headers["Content-Type"] = "application/json"
                cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % index
                return json.dumps(self.book[index])

            elif method == "DELETE":
                return self.delete(index)

            else:
                cherrypy.response.headers["Allow"] = "GET, DELETE"
                raise cherrypy.HTTPError(405)

        else:
            if method == "GET":
                if not state in self.book[index]:
                    raise cherrypy.HTTPError(404, "The specified resource is not currently available.")

                path = self.book[index][state]
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

        for imagePath in self.book[index].values():
            os.unlink(resources.filePath(imagePath))
        self.book.pop(index)
        return

        
class ExportController(object):

    book = None
    generatedPDFPath = None
    pdfGenerator = None
    
    def __init__(self, book):
        self.pdfGenerator = pdf.PDFGenerator(resources)
        self.book = book
        
    @cherrypy.expose
    def default(self, name=None, images=[]):
        method = cherrypy.request.method.upper()
        if method == "GET":
            # TODO: We should probably look on the file system for this,
            # rather than just assuming we've got a reference to in memory.
            if self.generatedPDF != None:
                # TODO: Perhaps we should do an HTTP redirect to the actual resource here.
                file = open(resources.filePath(self.generatedPDFPath))
                content = file.read()
                file.close()
                return content
            else:
                raise cherrypy.HTTPError(404, 
                                         "A PDF has not been generated yet, \
                                         so the specified resource is not yet avaiable.")
            
        elif method == "POST":
            # TODO: We know all the pages in the book already, why read them from the request?
            try:
                self.generatedPDFPath = self.pdfGenerator.generate(self.book)
                return resources.webURL(self.generatedPDFPath)
            except pdf.PDFGenerationError:
                raise cherrypy.HTTPError(500, "Could not create PDF." )
        else:
            cherrypy.response.headers["Allow"] = "GET, POST"
            raise cherrypy.HTTPError(405)
        

class DecapodServer(object):

    cameraSource = None
    book = []
    
    def __init__(self, cameras):
        self.cameraSource = cameras
        
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect(resources.webURL("${components}/bookManagement/html/bookManagement.html"))

    @cherrypy.expose
    def cameras(self):
        cameraStatus = self.cameraSource.status()
        cherrypy.response.headers["Content-type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename=CameraStatus.json"
        return json.dumps(cameraStatus)


# Package-level utility functions for starting the server.
def parseClassNamePath(classNamePath):
    pathSegs = classNamePath.split(".")
    assert 2, len(pathSegs)
    return pathSegs[0], pathSegs[1]

def determineCamerasClass():
    if len(sys.argv) > 1 and sys.argv[1] == "--no-cameras":
        return "cameras.MockCameras"
    else:
        return "cameras.Cameras"
    
def mountApp(camerasClassName):    
    moduleName, className = parseClassNamePath(camerasClassName)
    camerasModule = globals()[moduleName]
    cameraClass = getattr(camerasModule, className)
    
    root = DecapodServer(cameraClass(resources,
                                     "${config}/decapod-supported-cameras.json"))
    root.images = ImageController(root.cameraSource, root.book)
    root.pdf = ExportController(root.book)
    cherrypy.tree.mount(root, "/", resources.cherryPyConfig())
    return root
        
def startServer():
    cherrypy.engine.start()
    
if __name__ == "__main__":
    mountApp(determineCamerasClass())
    startServer()
    