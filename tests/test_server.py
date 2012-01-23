import cherrypy
from cherrypy.test import helper

import os.path
import sys
sys.path.append(os.path.abspath('..'))
import decapod

class TestREST(helper.CPWebCase):
        
    def setup_server():
        decapod.mountApp()
    setup_server = staticmethod(setup_server)
    
    # Decapod 0.5 REST URL Spec 
    #    /: GET
    #    /library/: NONE
    #    /library/'bookName': DELETE
    #    /library/'bookName'/pages: POST
    #    /library/'bookName'/export: GET, PUT, DELETE
     
    def test_01_getRoot(self):
#        self.setup_class()
#        cherrypy.engine.block()
        expectedRedirectURL = "/components/import/html/Import-05a.html"
        
        self.getPage("/")
        self.assertStatus(303, "Should return a 303 'See Other' status for the redirect")
        self.assertHeader("Location", cherrypy.url(expectedRedirectURL), "Assert that the Location is set to the redirect URL")
        
    def test_02_redirectURL(self):
        expectedRedirectURL = "/components/import/html/Import-05a.html"
        
        self.getPage(expectedRedirectURL)
        self.assertStatus(200, "Should return a 200 'OK' status")
        
