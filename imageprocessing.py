import os
from PIL import Image
import decapod_utilities as utils

class ImageProcessingError(Exception): pass

class ImageProcessor(object):
    
    resources = None
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
    
    def resize(self, imagePath, newLongestDimension, resizedImagePath = None, filter = Image.NEAREST):
        resizedImagePath = imagePath if resizedImagePath is None else resizedImagePath
        fullImagePath = self.resources.filePath(imagePath)
        im = Image.open(fullImagePath)
        size = im.size
        longestDim = size[1] if size[1] > size[0] else size[0]
        resizeFactor = float(newLongestDimension) / float(longestDim)
        newSize = (int(size[0] * resizeFactor), int(size[1] * resizeFactor))
        resized = im.resize(newSize, filter)
        resized.save(self.resources.filePath(resizedImagePath))
        return resizedImagePath
    
    def medium(self, imagePath):
        midPath = self.resources.appendSuffix(imagePath, "-mid")
        return self.resize(imagePath, 800, midPath) 
    
    def thumbnail(self, fullSizeImagePath):
        size = 100, 146
        im = Image.open(self.resources.filePath(fullSizeImagePath))
        im.thumbnail(size, Image.ANTIALIAS)
        thumbnailPath = self.resources.appendSuffix(fullSizeImagePath, "-thumb")
        im.save(self.resources.filePath(thumbnailPath))
        return thumbnailPath
    
    def stitch(self, firstImagePath, secondImagePath):
        # The stitched file should be named as a concatenation of the two image names.
        stitchFileName = self.resources.getFileName(firstImagePath)[0] \
                         + "-" + \
                         self.resources.getFileName(secondImagePath)[0] \
                         + ".png"
        
        # Save the stitched image in the same location as the first image.
        stitchFilePath = self.resources.getPathHead(firstImagePath) + stitchFileName
        
        # Stitch the images together.
        absFirstPath = self.resources.filePath(firstImagePath)
        absSecondPath = self.resources.filePath(secondImagePath)
        absStitchPath = self.resources.filePath(stitchFilePath)
        
        stitchCmd = [
            "decapod-stitching",
            "-Rnn",
            absFirstPath,
            absSecondPath,
            "-o",
            absStitchPath   
        ]
        utils.invokeCommandSync(stitchCmd, ImageProcessingError, "An error occurred while trying to stitch images.")
        return stitchFilePath
    