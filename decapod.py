
# TODO: File system or CouchDB persistence for the Book, including:
#   * the images array
#   * the calibration model

import cherrypy
import os
import simplejson as json
import sys

import resourcesource
import imageprocessing
import cameras
import pdf

# Setup configuration for static resources within the server.
DECAPOD_CONFIG = os.path.join(resourcesource.serverBasePath, "config/decapod-resource-config.json")

class ImageController(object):
    """Main class for manipulating images.

    Exposes operations such as capturing, post-processing and deleting pictures
    and sets of pictures. All URLs are considered a path to an image or to a set
    of images represented by a JSON file of their attributes."""
    resources = None
    cameraSource = None
    book = None
    
    def __init__(self, resourceSource, cameras, book):
        self.resources = resourceSource
        self.cameraSource = cameras
        self.book = book
        
    def createPageModelForWeb(self, bookPage):
        webModel = {}
        for image in bookPage.keys():
            webModel[image] = self.resources.webURL(bookPage[image])
        return webModel
        
    def capturePageSpread(self):
        # TODO: Image processing pipeline should not be in the controller       
        firstImagePath, secondImagePath = self.cameraSource.capturePageSpread()
        absFirstImagePath = self.resources.filePath(firstImagePath)
        absSecondImagePath = self.resources.filePath(secondImagePath)
        
        firstMidPath = imageprocessing.medium(absFirstImagePath)
        secondMidPath = imageprocessing.medium(absSecondImagePath)
        stitchedPath = imageprocessing.stitch(firstMidPath, secondMidPath)
        thumbnailPath = imageprocessing.thumbnail(stitchedPath)

        page = {
            "left": firstImagePath,
            "right": secondImagePath,
            "spread": self.resources.virtualPath(stitchedPath),
            "thumb": self.resources.virtualPath(thumbnailPath)
        }
        self.book.append(page)
        return page
        
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
            webBook = map(self.createPageModelForWeb, self.book)
            return json.dumps(webBook)

        elif method == "POST":
            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % len(self.book)
            pageSpread = self.capturePageSpread()
            return json.dumps(self.createPageModelForWeb(pageSpread))

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
            os.unlink(self.resources.filePath(imagePath))
        self.book.pop(index)
        return

class CamerasController(object):
    
    resources = None
    cameraSource = None
    
    def __init__(self, resourceSource, cameraSource):
        self.resources = resourceSource
        self.cameraSource = cameraSource
        
    @cherrypy.expose()
    def index(self):
        cameraStatus = self.cameraSource.status()
        cherrypy.response.headers["Content-type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename=CameraStatus.json"
        return json.dumps(cameraStatus)
    
class CalibrationController(object):
    
    resources = None
    cameraSource = None
    processor = None
    calibrationImages = {}
    
    def __init__(self, resourceSource, cameraSource):
        self.resources = resourceSource
        self.cameraSource = cameraSource
        
    @cherrypy.expose()  
    def index(self, calibrationModel=None):
        method = cherrypy.request.method.upper()
        if method == "GET":
            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Calibration.json"
            calibrationModel = self.cameraSource.calibrationModel()
            return json.dumps(calibrationModel)
        elif method == "POST":
            self.cameraSource.calibrationModel(json.loads(calibrationModel))
            return calibrationModel
        else:
            cherrypy.response.headers["Allow"] = "GET, POST"
            raise cherrypy.HTTPError(405)
    
    def captureCalibrationImage(self, cameraName):
        # TODO: Image processing pipeline code shouldn't be in controller code!
        calibrationImagePath = self.cameraSource.captureCalibrationImage(cameraName)
        imageprocessing.resize(calibrationImagePath, 640)
        return calibrationImagePath
        
    def calibrationImageHandler(self, cameraName):
        jsonImage = lambda : json.dumps({"image": self.resources.webURL(self.calibrationImages[cameraName])})
        method = cherrypy.request.method.upper()
        if method == "GET":
            return jsonImage()
        elif method == "PUT":
            self.calibrationImages[cameraName] = self.captureCalibrationImage(cameraName)
            return jsonImage()
        else:
            cherrypy.response.headers["Allow"] = "GET, PUT"
            raise cherrypy.HTTPError(405)
        
    @cherrypy.expose()
    def left(self):
        return self.calibrationImageHandler("left")
    
    @cherrypy.expose()
    def right(self):
        return self.calibrationImageHandler("right")
            
            
class ExportController(object):

    resources = None
    book = None
    generatedPDFPath = None
    pdfGenerator = None
    
    def __init__(self, resourceSource, book):
        self.resources = resourceSource
        self.pdfGenerator = pdf.PDFGenerator(self.resources)
        self.book = book
        
    @cherrypy.expose
    def default(self, name=None, images=[]):
        method = cherrypy.request.method.upper()
        if method == "GET":
            # TODO: We should probably look on the file system for this,
            # rather than just assuming we've got a reference to in memory.
            if self.generatedPDF != None:
                # TODO: Perhaps we should do an HTTP redirect to the actual resource here.
                file = open(self.resources.filePath(self.generatedPDFPath))
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
                return self.resources.webURL(self.generatedPDFPath)
            except pdf.PDFGenerationError:
                raise cherrypy.HTTPError(500, "Could not create PDF." )
        else:
            cherrypy.response.headers["Allow"] = "GET, POST"
            raise cherrypy.HTTPError(405)
        

class DecapodServer(object):

    resources = None
    cameraSource = None
    book = []
    
    def __init__(self, resourceSource, cameras):
        self.resources = resourceSource
        self.cameraSource = cameras
        
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect(self.resources.webURL("${components}/bookManagement/html/bookManagement.html"))


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
    # Parse command line options, configuring the correct cameras object    
    moduleName, className = parseClassNamePath(camerasClassName)
    camerasModule = globals()[moduleName]
    cameraClass = getattr(camerasModule, className)
    
    # Set up shared resources
    resources = resourcesource.ResourceSource(DECAPOD_CONFIG)
    cameraSource = cameraClass(resources, "${config}/decapod-supported-cameras.json")
    
    # Set up the server application and its controllers
    root = DecapodServer(resources, cameraSource)
    root.images = ImageController(resources, cameraSource, root.book)
    root.pdf = ExportController(resources, root.book)
    root.cameras = CamerasController(resources, cameraSource)
    root.cameras.calibration = CalibrationController(resources, cameraSource)
    
    # Mount the application
    cherrypy.tree.mount(root, "/", resources.cherryPyConfig())
    return root
        
def startServer():
    cherrypy.engine.start()
    
if __name__ == "__main__":
    mountApp(determineCamerasClass())
    startServer()
    