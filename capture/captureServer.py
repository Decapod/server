import cherrypy
import os
import sys
import simplejson as json

import cameras
import status
import capture
import cameraInterface
import mockCameraInterface

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import backgroundTaskQueue
from utils import server, io

# Setup for Decapod's cherrypy configuration file.
CURRENT_DIR = os.getcwd()
DECAPOD_CONFIG_FILE = os.path.abspath(os.path.join("config", "captureServer.conf"))

# Determine if the server is running under an SCGI-WSGI interface
IS_SCGIWSGI = (sys.argv[0] == 'scgi-wsgi')

# Subscribe to BackgroundTaskQueue plugin
bgtask = backgroundTaskQueue.BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()

# Defines and calculates the data directories of all capture types
CONVENTIONAL_DATA_DIR = os.path.join("${data}", "conventional")
STEREO_DATA_DIR = os.path.join("${data}", "stereo")
STRUCTURED_DATA_DIR = os.path.join("${data}", "structured")

CAPTURE_STATUS_FILENAME = "captureStatus.json"

def startServer():
    '''
    Starts the cherrypy server and sets up the necessary signal handlers for running from the command line
    '''
    # mount app
    root = mountApp()

    # subscribe to a signal handler.
    # used for quitting the app via command line
    if hasattr(cherrypy.engine, 'signal_handler'):
        cherrypy.engine.signal_handler.subscribe()
        
    # subscribe to a console control handler.
    # used for quitting the app via command line on windows   
    if hasattr(cherrypy.engine, "console_control_handler"): 
        cherrypy.engine.console_control_handler.subscribe() 
    
    cherrypy.engine.subscribe('stop', releaseCameras)
    
    # start the server
    cherrypy.engine.start()
    
    # Block if running standalone, nut under an SCGI-SWGI interface
    if (not IS_SCGIWSGI) :
        cherrypy.engine.block()

def releaseCameras():
    '''
    The handler function for cherrypy shutdown listener to release all the cameras that have been prepared for simultaneous capture.
    '''
    cameraController = cameraInterface if not cherrypy.config["app_opts.general"]["testmode"] else mockCameraInterface
    cameraController.releaseCameras()
    
def mountApp(config=DECAPOD_CONFIG_FILE):
    '''
    Mounts the app and updates the cherryp configuration from the provided config file.
    Is used by startServer to start the cherrypy server, but can be called independently 
    if another process starts cherrypy (e.g. when run in the unit tests).
    '''
    # Set up the server application and its controllers
    root = CaptureServer()
    
    # update the servers configuration (e.g. sever.socket_host)
    cherrypy.config.update(config)
    
    # mount the app
    cherrypy.tree.mount(root, "/", config)

    return root

def convertPathToURL(capture):
    '''
    Used by map() function to convert a list of file paths to a list of URLs
    '''
    return server.getURL(cherrypy, capture, CURRENT_DIR)
        
class CaptureServer(object):
    '''
    Handler for the / resource
    
    Redirects requests to the root url to the apps start page.
    '''
    exposed = True
        
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        # converts abstract data directories defined for each type into actual physical dirs
        self.conventionalDir = rs.path(CONVENTIONAL_DATA_DIR)
        self.stereoDir = rs.path(STEREO_DATA_DIR)
        self.structuredDir = rs.path(STRUCTURED_DATA_DIR)

        self.paths = {
            "cameras": CamerasController(),
            "conventional": TypeController(self.conventionalDir),
            "stereo": TypeController(self.stereoDir)
        }

        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

    def GET(self):
        raise cherrypy.HTTPRedirect(rs.url("${components}/cameras/html/cameras.html    "), 301)
    
class CamerasController(object):
    '''
    Parses the positional arguments starting after /cameras/
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self):
        self.cameras = cameras.Cameras(cherrypy.config["app_opts.general"]["testmode"])
        
    def GET(self, *args, **kwargs):
        #returns the info of the detected cameras
        server.setAttachmentResponseHeaders(cherrypy, "camerasSummary.json", "application/json")
        return json.dumps(self.cameras.getCamerasSummary())

class TypeController(object):
    '''
    Parses the positional arguments starting after /[conventional|stereo]/
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self, typeDir):
        self.captureType = capture.Capture(typeDir, CAPTURE_STATUS_FILENAME, cherrypy.config["app_opts.general"])
        
        self.paths = {
            "cameras": TypeCamerasController(self.captureType),
            "capture": CaptureController(self.captureType)
        }
        
    def GET(self, *args, **kwargs):
        #returns the info of the detected cameras
        server.setAttachmentResponseHeaders(cherrypy, 'captureInfo.json', "application/json")
        return self.captureType.getStatus()

    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

class TypeCamerasController(object):
    '''
    Parses the positinal arguments starting after /[conventional|stereo]/capture/images
    If /images/ isn't followed by an index it raises an error.
    '''
    
    exposed = True
    
    def __init__(self, captureType):
        self.captureType = captureType
    
    def GET(self, *args):
        server.setAttachmentResponseHeaders(cherrypy, "cameras.json", "application/json")
        cherrypy.response.status = 200
        return json.dumps(self.captureType.getCamerasStatus())

class CaptureController(object):
    '''
    Parses the positional arguments starting after /[conventional|stereo]/capture
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self, captureType):
        self.captureType = captureType
        self.paths = {
            "images": ImagesController(self.captureType)
        }
        
    def GET(self, *args, **kwargs):
        # returns a zip file of all the captured images, and calibration data if found
        zipContent = io.readFromFile(self.captureType.export())
        
        if zipContent is not None:
            server.setAttachmentResponseHeaders(cherrypy, "capture.zip", "application/zip")
            cherrypy.response.status = 200
            return zipContent
        

    def POST(self, *args, **kwargs):
        try:
            captureIndex, captures = self.captureType.capture()
        except capture.CaptureError as e:
            raise cherrypy.HTTPError(500, e.message)
        except capture.CameraPortsChangedError as e:
            raise cherrypy.HTTPError(500, json.dumps(e.message))
        except Exception as e:
            raise cherrypy.HTTPError(500, e.message)
        
        # convert the capture file path to URL
        captureURLs = map(convertPathToURL, captures)
        
        server.setAttachmentResponseHeaders(cherrypy, 'imageLocations.json', "application/json")
        cherrypy.response.status = 202
        
        return json.dumps({"captureIndex": captureIndex, "captures": captureURLs})
        
    def DELETE(self, *args, **kwargs):
        self.captureType.delete()
        cherrypy.response.status = 204
        
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

class ImagesController(object):
    '''
    Parses the positinal arguments starting after /[conventional|stereo]/capture/images
    If /images/ isn't followed by an index it raises an error.
    '''
    
    exposed = True
    
    def __init__(self, captureType):
        self.captureType = captureType
    
    def DELETE(self, *args):
        self.captureType.deleteImages()
        cherrypy.response.status = 204

    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        return ImageIndexController(self.captureType, vpath[0])

class ImageIndexController(object):
    '''
    Parses the positinal arguments starting after /[conventional|stereo]/capture/images
    If /images/ isn't followed by an index it raises an error.
    '''
    
    exposed = True
    
    def __init__(self, captureType, imageIndex):
        self.captureType = captureType
        self.imageIndex = imageIndex
    
    def GET(self, *args):
        if self.imageIndex.isdigit():
            # Converts the image file paths to URLs
            imageURLs = map(convertPathToURL, self.captureType.getImagesByIndex(self.imageIndex))
            
            server.setAttachmentResponseHeaders(cherrypy, "images.json", "application/json")
            return json.dumps({"images": imageURLs})
        else:
            raise cherrypy.HTTPError(405)
    
    def DELETE(self, *args):
        if self.imageIndex.isdigit():
            self.captureType.deleteImagesByIndex(self.imageIndex)
            cherrypy.response.status = 204
        else:
            raise cherrypy.HTTPError(405)
    
if __name__ == "__main__":
    startServer()
    
