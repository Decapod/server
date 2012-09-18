import cherrypy
import os
import sys
import simplejson as json

import cameras
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

#subscribe to BackgroundTaskQueue plugin
bgtask = backgroundTaskQueue.BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()
       
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
#    root.cameras = CamerasController()
#    root.conventional = ConventionalController()
    
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
        self.paths = {
            "cameras": CamerasController(),
            "conventional": ConventionalController()
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
        server.setJSONResponseHeaders(cherrypy, "camerasSummary.json")
        return json.dumps(self.cameras.getCamerasSummary())

class ConventionalController(object):
    '''
    Parses the positional arguments starting after /conventional/
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    def __init__(self):
        self.conventional = conventional.Conventional(cherrypy.config["app_opts.general"]["testmode"])
        
    def GET(self, *args, **kwargs):
        #returns the info of the detected cameras
        server.setJSONResponseHeaders(cherrypy, 'conventionalInfo.json')
        return self.conventional.getStatus()

if __name__ == "__main__":
    startServer()
    
