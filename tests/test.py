import os.path
import sys
sys.path.append(os.path.abspath('..'))
from mockserver import *
from cherrypy.test import test as cptest

def run():
    # Update this list with new tests cases.
    # TODO: Do this dynamically by trawling the filesystem looking for test_*.py files.
    test_list = [
        "test_resourcesource", 
        "test_imageprocessing", 
        "test_cameras", 
        "test_server"
    ]
    
    cptest.CommandLineParser(test_list).run()

if __name__ == '__main__':
    run()
    