import cherrypy
import os
import sys
import simplejson as json

import dewarpProcessor

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

# Defines and calculates the data directory
DATA_DIR = os.path.join("${data}")
STATUS_FILE = os.path.join(DATA_DIR, "status.json")

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
    
def mountApp(config=DECAPOD_CONFIG_FILE):
    '''
    Mounts the app and updates the cherryp configuration from the provided config file.
    Is used by startServer to start the cherrypy server, but can be called independently 
    if another process starts cherrypy (e.g. when run in the unit tests).
    '''
    # Set up the server application and its controllers
    root = DewarpServer()
    
    # update the servers configuration (e.g. sever.socket_host)
    cherrypy.config.update(config)
    
    # mount the app
    cherrypy.tree.mount(root, "/", config)

    return root
        
class DewarpServer(object):
    '''
    Handler for the / resource
    
    Redirects requests to the root url to the apps start page.
    '''
    exposed = True

    def GET(self):
        raise cherrypy.HTTPRedirect(rs.url("${components}/dewarp/html/dewarp.html"), 301)
    
   # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        self.dataDir = rs.path(DATA_DIR)
        self.statusFile = rs.path(STATUS_FILE)
        self.dewarpProcessor = dewarpProcessor.DewarpProcessor(self.dataDir, self.statusFile)

        self.paths = {
            "captures": CapturesController(self.dewarpProcessor),
            "dewarpedArchive": DewarpedArchiveController(self.dewarpProcessor)
        }

        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

class CapturesController(object):
    '''
    Handler for the /captures resource
    '''
    
    exposed = True
    
    def __init__(self, dewarpProcessor):
        self.dewarpProcessor = dewarpProcessor
        
    def GET(self):
        try:
            status = self.dewarpProcessor.getArchiveStatus()
        except dewarpProcessor.UnpackedDirNotExistError as e:
            raise cherrypy.HTTPError(404)
        
        if status.get("ERROR_CODE"):
            cherrypy.response.status = 500
        else:
            cherrypy.response.status = 200
            
        server.setAttachmentResponseHeaders(cherrypy, "captures.json", "application/json")
        return json.dumps(status)
    
    def PUT(self, *args, **kwargs):
        try:
            status = self.dewarpProcessor.unzip(kwargs["file"])
        except dewarpProcessor.DewarpInProgressError as e:
            raise cherrypy.HTTPError(409, e.message)
        
        server.setAttachmentResponseHeaders(cherrypy, "captures.json", "application/json")
        cherrypy.response.status = 200
        return json.dumps(status)

    def DELETE(self):
        try:
            self.dewarpProcessor.deleteUpload()
        except dewarpProcessor.DewarpInProgressError as e:
            raise cherrypy.HTTPError(409, e.message)
        
        cherrypy.response.status = 204
        
class DewarpedArchiveController(object):
    '''
    Handler for the /dewarpedArchive resource
    '''
    
    exposed = True
    
    def __init__(self, dewarpProcessor):
        self.dewarpProcessor = dewarpProcessor
        
    def GET(self):
        status = self.dewarpProcessor.getStatus()
        if status.get("status") == "complete":
            status["url"] = server.getURL(cherrypy, self.dewarpProcessor.export, CURRENT_DIR)
        server.setAttachmentResponseHeaders(cherrypy, "status.json", "application/json")
        return json.dumps(status)
    
    def DELETE(self):
        try:
            self.dewarpProcessor.delete()
        except dewarpProcessor.DewarpInProgressError as e:
            raise cherrypy.HTTPError(409, e.message)
        
        cherrypy.response.status = 204
        
    def PUT(self, *args, **kwargs):
        bgtask.put(self.dewarpProcessor.dewarp)
        cherrypy.response.status = 202

if __name__ == "__main__":
    startServer()
    
