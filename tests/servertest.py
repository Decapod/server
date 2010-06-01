import cherrypy
import os
from cherrypy.test import helper
import sys
sys.path.append(os.path.abspath('..'))
import mockserver

class ServerTest(helper.CPWebCase):
    """
    Is the same as helper.CPWebCase
    """

def setup_mockserver():
    #Starts up the server
    parent = os.path.abspath(os.path.dirname('../'))
    configPath = os.path.join(parent, 'dserver.conf')
    root = mockserver.MockServer()
    root.images = mockserver.ImageController()
    root.pdf = mockserver.Export()
    #cherrypy.quickstart(root, "/", configPath)
    cherrypy.tree.mount(root, "/", configPath)