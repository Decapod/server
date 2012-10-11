import sys
import os
import imghdr

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource
import utils

IMPORT_DIR = "${library}/book/images/"

# Exception classes
class ImportTypeError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class ImageImport(object):

    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.importDir = self.rs.path(IMPORT_DIR)
                
        # Setup the import location.
        utils.io.makeDirs(self.importDir)
    
    def isValidType(self, file, validTypes=["jpeg", "png", "tiff"]):
        '''
        Returns a boolean indicating if the file is one of the specified validTypes
        '''
        realType = imghdr.what(file)
        return realType in validTypes
    
    def save(self, file, name=None):
        ''' 
        Saves the file with the given name. 
        If no name is provided it will call genearteImageName to create one
        
        Exceptions
        ==========
        ImportTypeError: if the file is not of a valid type ["jpeg", "png", "tiff"]
        '''
        fileType = utils.io.getFileType(file)
        name = name if name else utils.image.generateImageName(suffix=fileType)
        imagePath = os.path.join(self.importDir, name)
        utils.io.writeStreamToFile(file, imagePath)
        if not self.isValidType(imagePath):
            utils.io.rmFile(imagePath)
            raise ImportTypeError("The file ({0}) must be a valid 'jpeg', 'png', or 'tiff'".format(name))
        
        return imagePath
