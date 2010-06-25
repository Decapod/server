import os.path
import sys
sys.path.append(os.path.abspath('..'))
from mockserver import *
from cherrypy.test import test as cptest

def run():
    #exectues tests suites
    test_list = ["test_resourcesource", "test_imageprocessing", "test_server"]
    cptest.CommandLineParser(test_list).run()

if __name__ == '__main__':
    run()
    