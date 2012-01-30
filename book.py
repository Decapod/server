import os
import shutil
import decapod_utilities as utils
import resourcesource

BOOK_DIR = "${library}/book/"

class Book(object):

    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.bookDir = self.rs.path(BOOK_DIR)
        
    def delete(self):
        if os.path.exists(self.bookDir):
            shutil.rmtree(self.bookDir)
