"""Module contains a fully operable stand-alone Decapod server.

It provides a resource-oriented approach to working with images (capturing,
deleting, generating thumbnails). It can be used with any client using the
provided uniform interface for accessing and modifying images.
"""

import dserver_env
import cherrypy
import glob
import os
import simplejson as json
import sys
from PIL import Image

imageIndex = 0
#TODO: change to a better path FLUID-3538
imagePath = os.path.join(dserver_env.server_dir, "testData/capturedImages")

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
        collection (POST). Also supports changing the list of images (PUT)"""

        method = cherrypy.request.method.upper()
        if method == "GET":
            cherrypy.response.headers["Content-Type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename='Captured images.json'"
            return json.dumps(self.images)

        elif method == "POST":

            # TODO: remove the ports and models param lookup, and assertions.
            params = cherrypy.request.params
            ports, models = [None, None], [None, None]
            if "ports" in params and "models" in params:
                ports, models = params["ports"], params["models"]
            
            assert len(ports) >= 2
            assert len(models) >= 2

            first_image  = self.take_picture(found_cameras[0]["port"], found_cameras[0]["model"])
            second_image = self.take_picture(found_cameras[1]["port"], found_cameras[1]["model"])

            cherrypy.response.headers["Content-type"] = "application/json"
            cherrypy.response.headers["Content-Disposition"] = "attachment; filename=Image%d.json" % len(self.images)
            model_entry = {"left": first_image, "right": second_image}

            #TODO: add page order correction.            

            model_entry["spread"] = self.stitchImages (first_image, second_image)
            model_entry["thumb"]  = self.generateThumbnail(model_entry["spread"])

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

    def take_picture(self, port=None, model=None):
        """Capture an image and save it to disk.

        If the application is in testing mode, do not use a camera. Instead, get
        an image from the local filesytem."""


        # Filename and directory declarations.
        captureFilename = 'newDecapodCapture.jpg'
        decapodImagePrefix = 'decapod'
        
        # Check save path for images.
        # TODO: move this to server initialization so it's only done once (FLUID-3537)
        # TODO: change the save location for files, and change the code that is depends on the directory being testdata/capturedImages/
        if not os.access (imagePath,os.F_OK) and os.access ("./",os.W_OK):
            status = os.system("mkdir %s" % imagePath)
            if status !=0:
                raise cherrypy.HTTPError(403, "Could not create path %s." % imagePath)
        elif not os.access ("./",os.W_OK):
            raise cherrypy.HTTPError(403, "Can not write to directory")

        status = os.system("gphoto2 --capture-image-and-download --force-overwrite --port=%s --camera='%s' --filename=%s 2>>capture.log" % (port, model,captureFilename))
        if status != 0:
            raise cherrypy.HTTPError(500, "Camera could not capture.")
        
        # create new filename for image.
        # TODO: Move filename generation to a new function. FLUID-3538
        global imageIndex
        imageIndex += 1
        
        #TODO: change newFilename = '%s-%04d.jpg' % (decapodImagePrefix,imageIndex) FLUID-3538
        newFilename = 'Image%d.jpg' % imageIndex

        status = os.system("mv -f %s %s/%s" % (captureFilename,imagePath,newFilename))
        if status != 0:
            raise cherrypy.HTTPError(500, "Could not rename file %s to %s/%s" % (captureFilename,imagePath,newFilename))

        newFilePath = '%s/%s' % (imagePath,newFilename)
        return newFilePath

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
        thumbnailPath = filepath[:-4] + "-thumb.jpg"
        im.save(thumbnailPath)
        return thumbnailPath

    def stitchImages (self, image_one, image_two):
        stitchFilename = image_one.split('/').pop()
        stitchFilename = stitchFilename[:-4] + "-" +image_two.split('/').pop()
        stitchFilepath = imagePath + "/" + stitchFilename[:-4] + ".png"

        #Image Magick implementation
        #os.system ("convert %s %s +append %s" % (image_one, image_two, stitchFilepath))

        #Decapod implementation
        os.system ("decapod-stitching %s %s -o %s" % (image_one, image_two, stitchFilepath))

        return stitchFilepath
        
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

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/capture")

    @cherrypy.expose
    def capture(self):
        # TODO: Hardcoded path. Remove it.
        html_path = os.path.join(dserver_env.server_dir, \
                                 "../decapod-ui/components/capture/html/Capture.html")
        file = open(html_path)
        content = file.read()
        file.close()
        return content

    @cherrypy.expose
    def cameras(self):
        """Detects the cameras locally attached to the PC.

        Returns a JSON document, describing the camera and its capabilities:
        model, port, download support, and capture support."""
        global found_cameras

        found_cameras = []
        status = os.system("gphoto2 --auto-detect | grep '^Model\|^-' -v >/tmp/output.tmp")
        if status != 0:
            return json.dumps(found_cameras)

        file = open("/tmp/output.tmp")
        for line in file:
            info = line.split()
            port = info.pop().rstrip("\n")
            if port.endswith(":"):
                continue
            model = " ".join(info)

            status = os.system("gphoto2 --summary --camera='%s' --port=%s" % (model, port))
            if status != 0:
                capture = False
                download = False
            else:
                status = os.system("gphoto2 --summary --camera='%s' --port=%s | grep 'Generic Image Capture'" % (model, port))
                capture = (status == 0)
                
                status = os.system("gphoto2 --summary --camera='%s' --port=%s | grep 'No File Download'" % (model, port))
                download = (status != 0)

            camera = {"model": model, "port": port, "capture": capture, "download": download}
            found_cameras.append(camera)


        file.close()

        cherrypy.response.headers["Content-type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename=found_cameras.json"
        return json.dumps(found_cameras)

if __name__ == "__main__":
    root = DecapodServer()
    root.images = ImageController()
    root.pdf = Export()
    cherrypy.quickstart(root, "/", "dserver.conf")
