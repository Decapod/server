
# TODO: File system or CouchDB persistence for the Book, including:
#   * the images array

import cherrypy
import os
import simplejson as json
import sys

import resourcesource
import pdf
import imageImport
import book
import pdfExport
import backgroundTaskQueue

# Setup configuration for static resources within the server.
DECAPOD_CONFIG = os.path.join(resourcesource.serverBasePath, "config/decapod-resource-config.json")

#subscribe to BackgroundTaskQueue plugin
bgtask = backgroundTaskQueue.BackgroundTaskQueue(cherrypy.engine)
bgtask.subscribe()

class ImportController(object):
    
    image, resource = None, None
    
    def __init__(self, resourceSource):
        self.resource = resourceSource
        self.image = imageImport.ImageImport(self.resource)
    
    @cherrypy.expose()
    def index(self, file):
        # import the file
        return self.image.save(file)

# TODO: move this to an appropriate location
# used to invoke a function by name
def invoke(obj, method, excption="405 Method Not Allowed", *args, **kwargs):
    try:
        func = getattr(obj, method)
    except AttributeError:
        raise cherrypy.HTTPError(exception)
    else:
        return func(*args, **kwargs)
    
def setJSONResponseHeaders(fileName="model.json"):
    cherrypy.response.headers["Content-Type"] = "application/json"
    cherrypy.response.headers["Content-Disposition"] = "attachment; filename='{0}'".format(fileName)

#TODO: Support GET requests to return the book's model
#TODO: Support PUT requests to update the books's model
#TODO: Update DELETE to remove the entire book directory, by name, and not just all the stored pages
class BookController(object):
    '''
    Handler for the /books/"bookName"/ resource
    
    Currently only handles DELETE requests, which result in all the pages being removed.
    '''

    exposed = True

    def __init__(self, resourceSource, name):
        self.resource = resourceSource
        self.name = name
        self.book = book.Book(self.resource)
        
    def GET(self):
        return "The BOOK model\n"
    
    def PUT(self):
        return "Create/Update and return the new Book model\n"
        
    def DELETE(self, *args, **kwargs):
        self.book.delete()

#TODO: Support GET requests to return the book's pages model
#TODO: Support PUT requests to update the book's pages model
#TODO: On post do more than just save the images, model data should also be added
class PagesController(object):
    '''
    Handler for the /books/"bookName"/pages resource
    
    Currently only handles POST requests, which results in new pages being added.
    This is useful for importing pages.
    '''
    
    page = None
    
    def __init__(self, resourceSource, bookName):
        self.resource = resourceSource
        self.bookName = bookName
        self.page = imageImport.ImageImport(self.resource)
    
    def post(self, *args, **kwargs):
        # import the file
        return self.page.save(kwargs["file"])

#TODO: Rename to ExportController when old one is no longer needed (will require refactoring or removing capture)
class ImportExportController(object):
    '''
    Handler for the /books/"bookName"/export resource
    '''
    types = dict(type1 = "1", type2 = "2", type3 = "3")
    def __init__(self, resourceSource, bookName):
        self.resource = resourceSource
        self.bookName = bookName
        self.export = pdfExport.PDFGenerator(self.resource)
        
    def get(self, *args, **kwargs):
        #returns the status and, if available, the url to the exported pdf
        setJSONResponseHeaders("exportStatus.json")
        return self.export.getStatus()
        
    def put(self, *args, **kwargs):
        #triggers the creation of the pdf export
        bgtask.put(self.export.generate, self.types[args[0]])
        return self.export.getStatus()
    
    def delete(self, *args, **kwargs):
        #removes the pdf export artifact
        self.export.deletePDF()
        return self.export.getStatus()

# Books controller
#class BooksController(object):
#    '''
#    Parses the positional arguments starting after the /books/
#    and calls the appropriate handlers for the various resources 
#    '''
#    
#    def __init__(self, resourceSource=None):
#        self.resource = resourceSource
#    
#    @cherrypy.expose()
#    def default(self, *args, **kwargs):
#        method = cherrypy.request.method.lower()
#        
#        if not args:
#            raise cherrypy.HTTPError("404 Not Found")
#        
#        if len(args) == 1:
#            book = BookController(self.resource, args[0])
#            return invoke(book, method, *args[1:], **kwargs)
#        
#        elif len(args) > 1:
#              
#            if args[1] == "pages":
#                #trigger pages resource handler
#                pages = PagesController(self.resource, args[0])
#                return invoke(pages, method, *args[2:], **kwargs)
#                
#            elif args[1] == "export":
#            #trigger export resource handler
#                export = ImportExportController(self.resource, args[0])
#                return invoke(export, method, *args[2:], **kwargs)
#            
#            else:
#                raise cherrypy.HTTPError("404 Not Found")
#        
#        else:
#            raise cherrypy.HTTPError("404 Not Found")

# Books Controller
# TODO: Direct dynamic URLs to the correct controller
# TODO: rename to Library
class BooksController(object):
    '''
    Parses the positional arguments starting after the /books/
    and calls the appropriate handlers for the various resources 
    '''
    
    exposed = True
    
    def __init__(self, resourceSource=None):
        self.resource = resourceSource
    
    def GET(self):
        return "The Books model\n"
    
    def POST(self):
        return "Create the Book and return the new Books model\n"
    
    def _cp_dispatch(self, vpath):
        print "_cp_dispatch - vpath: {0}".format(vpath)
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
    
def mountApp(resources):
    # Set up the server application and its controllers
    root = DecapodServer(resources)
    root.imageImport = ImportController(resources)
    
    #setup for Decapod 0.5a
    root.books = BooksController(resources)
    
    return root
        
def startServer():
    #set up shared resources
    resources = resourcesource.ResourceSource(DECAPOD_CONFIG)
    
    #mount app
    root = mountApp(resources)
    
    #start application
    cherrypy.quickstart(root, "/", resources.cherryPyConfig())
    
if __name__ == "__main__":
    startServer()
    
