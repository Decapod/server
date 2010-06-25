import os
from PIL import Image

class ImageProcessor(object):
    
    resources = None
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
        
    def thumbnail(self, fullSizeImagePath):
        size = 100, 146
        im = Image.open(self.resources.filePath(fullSizeImagePath))
        im.thumbnail(size, Image.ANTIALIAS)
        thumbnailPath = fullSizeImagePath[:-4] + "-thumb.jpg"
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
        os.system ("decapod-stitching %s %s -o %s" % (absFirstPath, \
                                                      absSecondPath, \
                                                      absStitchPath))
        return stitchFilePath
    