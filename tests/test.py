import os.path
import sys
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
    
    cptest.TestHarness(test_list).run()

if __name__ == '__main__':
    run()
    