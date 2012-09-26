import sys
import os

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource
from utils import io

BOOK_DIR = "${library}/book/"

class Book(object):

    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.bookDir = self.rs.path(BOOK_DIR)
        
    def delete(self):
        io.rmTree(self.bookDir)
