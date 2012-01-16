import os.path
import sys
import shutil
from cherrypy.test import test as cptest
import testutils

def run():
    # Update this list with new tests cases.
    # TODO: Do this dynamically by trawling the filesystem looking for test_*.py files.
    test_list = [
        "test_decapod_utilities",
        "test_resourcesource",
        "test_imageImport"
    ]
    
    cptest.TestHarness(test_list).run()
    testutils.deleteTestImagesDir()
    testutils.cleanUpDir("../book/images/")
    shutil.rmtree("../book/pdf/")
    
if __name__ == '__main__':
    run()
    