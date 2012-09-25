import cherrypy
import os
import sys
import simplejson as json

import cameras
import status
import conventional

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource as rs
import backgroundTaskQueue
from utils import server

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
    
    # start the server
    cherrypy.engine.start()
    
    # Block if running standalone, nut under an SCGI-SWGI interface
    if (not IS_SCGIWSGI) :
        cherrypy.engine.block()

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

class CaptureServer(object):
    '''
    Handler for the / resource
    
    Redirects requests to the root url to the apps start page.
    '''
    exposed = True
        
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        # converts abstract data directories defined for each type into actual physical dirs
        self.rs = rs
        self.conventionalDir = self.rs.path(CONVENTIONAL_DATA_DIR)
        self.stereoDir = self.rs.path(STEREO_DATA_DIR)
        self.structuredDir = self.rs.path(STRUCTURED_DATA_DIR)

        self.paths = {
            "cameras": CamerasController(),
            "conventional": ConventionalController(self.conventionalDir)
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
        a = 1
        
    def GET(self, *args, **kwargs):
        #returns the info of the detected cameras
        server.setJSONResponseHeaders(cherrypy, "camerasSummary.json")
        return json.dumps(self.cameras.getCamerasSummary())

class ConventionalController(object):
    '''
    Parses the positional arguments starting after /conventional/
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self, conventionalDir):
        self.conventional = conventional.Conventional(conventionalDir, CAPTURE_STATUS_FILENAME, cherrypy.config["app_opts.general"]["testmode"])
        
        self.paths = {
            "capture": ConventionalCaptureController(self.conventional)
        }
        
    def GET(self, *args, **kwargs):
        #returns the info of the detected cameras
        server.setJSONResponseHeaders(cherrypy, 'conventionalInfo.json')
        return self.conventional.getStatus()

    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

class ConventionalCaptureController(object):
    '''
    Parses the positional arguments starting after /conventional/capture
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self, conventional):
        self.conventional = conventional
        self.paths = {
            "images": ConventionalCaptureImagesController(self.conventional)
        }
        
    def GET(self, *args, **kwargs):
        # returns the zipped captured images
        server.setJSONResponseHeaders(cherrypy, 'capturedImages.zip')
        cherrypy.response.status = 202

    def POST(self, *args, **kwargs):
        server.setJSONResponseHeaders(cherrypy, 'imageLocations.json')
        cherrypy.response.status = 202
        return json.dumps(self.conventional.capture())
        
    def DELETE(self, *args, **kwargs):
        self.conventional.delete()
        cherrypy.response.status = 204
        
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]
        
class ConventionalCaptureImagesController(object):
    '''
    Parses the positinal arguments starting after /conventional/capture/images
    If /images/ isn't followed by an index it raises an error.
    '''
    
    exposed = True
    
    def __init__(self, conventional):
        self.conventional = conventional
    
    def GET(self, *args):
        if len(args) and args[0].isdigit():
            server.setJSONResponseHeaders(cherrypy, "images.json")
            cherrypy.response.status = 200
            return json.dumps({"images": self.conventional.getImagesByIndex(args[0], rs.path(CONVENTIONAL_DATA_DIR))})
        else:
            raise cherrypy.HTTPError(405)
    
    def DELETE(self, *args):
        if not len(args) or args[0].isdigit():
            raise cherrypy.HTTPError(405)
        else:
            #TODO: Implement
            pass
    
if __name__ == "__main__":
    startServer()
    
