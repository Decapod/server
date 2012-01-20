
# TODO: File system or CouchDB persistence for the Book, including:
#   * the images array

import cherrypy
import os
import simplejson as json
import sys

import resourcesource
import imageImport
import book
import pdf
import backgroundTaskQueue

# Setup configuration for static resources within the server.
DECAPOD_CONFIG = os.path.join(resourcesource.serverBasePath, "config/decapod-resource-config.json")

# Determine if the server is running under an SCGI-WSGI interface
IS_SCGIWSGI = (sys.argv[0] == 'scgi-wsgi')

#subscribe to BackgroundTaskQueue plugin
bgtask = backgroundTaskQueue.BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()
    
def setJSONResponseHeaders(fileName="model.json"):
    cherrypy.response.headers["Content-Type"] = "application/json"
    cherrypy.response.headers["Content-Disposition"] = "attachment; filename='{0}'".format(fileName)

#TODO: Support GET requests to return the book's model
#TODO: Support PUT requests to update the library's model
#TODO: Update DELETE to remove the entire book directory, by name, and not just all the stored pages
class BookController(object):
    '''
    Handler for the /library/"bookName"/ resource
    
    Currently only handles DELETE requests, which result in all the pages being removed.
    '''

    exposed = True

    def __init__(self, resourceSource, name):
        self.resource = resourceSource
        self.name = name
        self.book = book.Book(self.resource)
        self.paths = {
            "pages": PagesController(self.resource, self.name),
            "export": ImportExportController(self.resource, self.name)
        }
        
    def DELETE(self, *args, **kwargs):
        self.book.delete()
    
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
    
    def __init__(self, resourceSource, bookName):
        self.resource = resourceSource
        self.bookName = bookName
        self.page = imageImport.ImageImport(self.resource)
    
    def POST(self, *args, **kwargs):
        # import the file
        return self.page.save(kwargs["file"])

#TODO: Rename to ExportController when old one is no longer needed (will require refactoring or removing capture)
class ImportExportController(object):
    '''
    Handler for the /library/"bookName"/export resource
    '''
    
    exposed = True
    
    types = dict(type1 = "1", type2 = "2", type3 = "3")
    def __init__(self, resourceSource, bookName):
        self.resource = resourceSource
        self.bookName = bookName
        self.export = pdf.PDFGenerator(self.resource)
        
    def GET(self, *args, **kwargs):
        #returns the status and, if available, the url to the exported pdf
        setJSONResponseHeaders("exportStatus.json")
        return self.export.getStatus()
        
    def PUT(self, *args, **kwargs):
        #triggers the creation of the pdf export
        bgtask.put(self.export.generate, self.types[args[1]])
        return self.export.getStatus()
    
    def DELETE(self, *args, **kwargs):
        #removes the pdf export artifact
        self.export.deletePDF()
        setJSONResponseHeaders("exportStatus.json")
        return self.export.getStatus()

# Library Controller
# TODO: rename to Library
# TODO: Support GET requests to return the Library model
# TODO: Support POST requests to create a Book and return the new Library model
class LibraryController(object):
    '''
    Parses the positional arguments starting after /library/
    and calls the appropriate handlers for the various resources 
    '''
    
    exposed = True
    
    def __init__(self, resourceSource=None):
        self.resource = resourceSource
    
    # Continues cherrypy object traversal. Useful for handling dynamic URLs
    def _cp_dispatch(self, vpath):
        return BookController(self.resource, vpath[0])

class DecapodServer(object):
    exposed = True
    
    resources = None
    book = []
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
        
    def GET(self):
        # the old Decapod 0.4 start page
        #raise cherrypy.HTTPRedirect(self.resources.webURL("${components}/bookManagement/html/bookManagement.html"))
        raise cherrypy.HTTPRedirect(self.resources.webURL("${components}/import/html/Import-05a.html"))
    
def mountApp():
    #set up shared resources
    resources = resourcesource.ResourceSource(DECAPOD_CONFIG)
    
    # Set up the server application and its controllers
    root = DecapodServer(resources)
    root.library = LibraryController(resources)
    
    # mount the app
    cherrypy.tree.mount(root, "/", resources.cherryPyConfig())
    return root, resources
        
def startServer():
    # mount app
    root, resources = mountApp()

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
    
if __name__ == "__main__":
    startServer()
    
