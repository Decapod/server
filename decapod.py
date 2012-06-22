
# TODO: File system or CouchDB persistence for the Book, including:
#   * the images array

import cherrypy
import os
import sys

import resourcesource as rs
import imageImport
import book
import pdf
import backgroundTaskQueue

# Setup for Decapod's cherrypy configuration file.
CURRENT_DIR = os.getcwd()
DECAPOD_CONFIG_FILE = os.path.abspath("config/decapod.conf")

# Determine if the server is running under an SCGI-WSGI interface
IS_SCGIWSGI = (sys.argv[0] == 'scgi-wsgi')

#subscribe to BackgroundTaskQueue plugin
bgtask = backgroundTaskQueue.BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()
    
def setJSONResponseHeaders(fileName="model.json"):
    cherrypy.response.headers["Content-Type"] = "application/json"
    cherrypy.response.headers["Content-Disposition"] = "attachment; filename='{0}'".format(fileName)
       
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
    root = DecapodServer()
    root.library = LibraryController()
    
    # update the servers configuration (e.g. sever.socket_host)
    cherrypy.config.update(config)
    
    # mount the app
    cherrypy.tree.mount(root, "/", config)
    return root

class DecapodServer(object):
    '''
    Handler for the / resource
    
    Redirects requests to the root url to the apps start page.
    '''
    exposed = True
    book = []
        
    def GET(self):
        raise cherrypy.HTTPRedirect(rs.url("${components}/exporter/html/exporter.html"), 301)
    
# Library Controller
# TODO: Support GET requests to return the Library model
# TODO: Support POST requests to create a Book and return the new Library model
class LibraryController(object):
    '''
    Parses the positional arguments starting after /library/
    and calls the appropriate handlers for the various resources 
    '''
    exposed = True
    
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        return BookController(vpath[0])
    
#TODO: Support GET requests to return the book's model
#TODO: Support PUT requests to update the library's model
#TODO: Update DELETE to remove the entire book directory, by name, and not just all the stored pages
class BookController(object):
    '''
    Handler for the /library/"bookName"/ resource
    
    Currently only handles DELETE requests, which result in all the pages being removed.
    '''
    exposed = True

    def __init__(self, name):
        self.name = name
        self.book = book.Book()
        self.paths = {
            "pages": PagesController(self.name),
            "export": ExportController(self.name)
        }
        
    def DELETE(self, *args, **kwargs):
        self.book.delete()
        cherrypy.response.status = 204
    
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        pathSegment = vpath[0]
        
        if pathSegment in self.paths:
            return self.paths[pathSegment]

#TODO: Support GET requests to return the book's pages model
#TODO: Support PUT requests to update the book's pages model
#TODO: Update POST to save pages to the specified book, instead of to a global location
#TODO: On POST do more than just save the images, model data should also be added
class PagesController(object):
    '''
    Handler for the /library/"bookName"/pages resource
    
    Currently only handles POST requests, which results in new pages being added.
    This is useful for importing pages.
    '''
    exposed = True
    page = None
    
    def __init__(self, bookName):
        self.bookName = bookName
        self.page = imageImport.ImageImport()
    
    # TODO: Should return the weburl not the filesystem path
    def POST(self, *args, **kwargs):
        # import the file
        try:
            path = self.page.save(kwargs["file"])
        except imageImport.ImportTypeError as e:
            raise cherrypy.HTTPError(415, e.message)
        cherrypy.response.headers["Location"] = path
        cherrypy.response.status = 201

class ExportController(object):
    '''
    Handler for the /library/"bookName"/export resource
    '''
    exposed = True
    types = dict(type1 = "1", type2 = "2", type3 = "3")
    
    def __init__(self, bookName):
        self.bookName = bookName
        self.export = pdf.PDFGenerator()
        
    def GET(self, *args, **kwargs):
        #returns the status and, if available, the url to the exported pdf
        setJSONResponseHeaders("exportStatus.json")
        return self.export.getStatus()
        
    def PUT(self, *args, **kwargs):
        #triggers the creation of the pdf export
        bgtask.put(self.export.generate, self.types[args[1]])
        cherrypy.response.status = 202
        setJSONResponseHeaders("exportStatus.json")
        return self.export.getStatus()
    
    def DELETE(self, *args, **kwargs):
        #removes the pdf export artifact
        self.export.deletePDF()
        cherrypy.response.status = 204

if __name__ == "__main__":
    startServer()
    
