import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import colourPickerInterface
import mockColourPickerInterface
import utils

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

# Exception classes
class ImagesDirNotExistError(Exception): pass

class ColourPickerProcessor(object):
    
    def __init__(self, imagesDir, testmode=False):
        self.imagesDir = imagesDir
        self.colourPickerController = mockColourPickerInterface if testmode else colourPickerInterface
        
    def pickColours(self):
        '''
        Triggers the colour picker to launch
        
        Exceptions
        ==========
        ImagesDirNotExistError: if the images directory does not exist
        '''
        if not os.path.exists(self.imagesDir):
            raise ImagesDirNotExistError, "The images directory \"{0}\" does not exist".format(self.imagesDir)
        sampleImage = utils.image.findImages(self.imagesDir)[0]
        self.colourPickerController.launchColourPicker(sampleImage)
