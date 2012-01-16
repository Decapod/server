import os
import shutil
import decapod_utilities as utils

BOOK_DIR = "${book}/images/"

class Book(object):
    
    resources = None
    bookDir = None

    def __init__(self, resourceSource):
        self.resources = resourceSource
        self.bookDir = self.resources.filePath(BOOK_DIR)
        
    def delete(self):
        if os.path.exists(self.bookDir):
            shutil.rmtree(self.bookDir)
            os.mkdir(self.bookDir)
