import os
from PIL import Image
import decapod_utilities as utils
import resourcesource

class ImageProcessingError(Exception): pass

def resize(imagePath, newLongestDimension, resizedImagePath = None, filter = Image.NEAREST):
    resizedImagePath = imagePath if resizedImagePath is None else resizedImagePath
    fullImagePath = imagePath
    im = Image.open(fullImagePath)
    size = im.size
    longestDim = size[1] if size[1] > size[0] else size[0]
    resizeFactor = float(newLongestDimension) / float(longestDim)
    newSize = (int(size[0] * resizeFactor), int(size[1] * resizeFactor))
    resized = im.resize(newSize, filter)
    resized.save(resizedImagePath)
    return resizedImagePath

def medium(imagePath):
    midPath = resourcesource.appendSuffix(imagePath, "-mid")
    return resize(imagePath, 800, midPath) 

def thumbnail(fullSizeImagePath):
    size = 100, 146
    im = Image.open(fullSizeImagePath)
    im.thumbnail(size, Image.ANTIALIAS)
    thumbnailPath = resourcesource.appendSuffix(fullSizeImagePath, "-thumb")
    im.save(thumbnailPath)
    return thumbnailPath

def stitch(firstImagePath, secondImagePath):
    # The stitched file should be named as a concatenation of the two image names.
    stitchFileName = resourcesource.parseFileName(firstImagePath)[0] \
                     + "-" + \
                     resourcesource.parseFileName(secondImagePath)[0] \
                     + ".png"
    
    # Save the stitched image in the same location as the first image.
    stitchFilePath = resourcesource.parsePathHead(firstImagePath) + stitchFileName
    
    # Stitch the images together.    
    stitchCmd = [
        "decapod-stitching",
        "-Rnn",
        firstImagePath,
        secondImagePath,
        "-o",
        stitchFilePath   
    ]
    utils.invokeCommandSync(stitchCmd, ImageProcessingError, "An error occurred while trying to stitch images.")
    return stitchFilePath
    
def rotate(imagePath, rotationDegrees):
    im = Image.open(imagePath)
    rotated = im.rotate(rotationDegrees)
    rotated.save(imagePath)
    return imagePath