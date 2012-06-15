import os
import decapod_utilities as utils
import imghdr

BOOK_DIR = "${library}/book/images/"
PDF_DIR = BOOK_DIR + "pdf/"

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_NONE = "none"

# TODO: Move these values into configuration
multiPageTIFFName = "Decapod-multipage.tiff"
pdfName = "Decapod.pdf"
statusFileName = "exportStatus.json"
tiffDir = "tiffTemp"
tempDir = "genPDFTemp"

class TIFFConversionError(Exception): pass
class TIFFImageError(Exception): pass
    
def isImage(filePath):
    return os.path.isfile(filePath) and imghdr.what(filePath) != None

def convertImage(imagePath, outputDir=None):
    '''
    Converts the image at imagePath into a tiff image.
    Can optionaly specify the directory where to save the new file, will default to the same directory as the original file.
    Returns the path to the new image file.
    
    Exceptions:
    TIFFImageError: if the file at imagePath isn't a supported image format
    TIFFConversionError: an error occurs during the conversion process
    '''
    if isImage(imagePath):
        ext = ".tiff"
        origDir, fileName = os.path.split(imagePath)
        name = os.path.splitext(fileName)[0]
        writeDir = outputDir if outputDir != None else origDir
        
        writePath = os.path.join(writeDir, name + ext)
        utils.invokeCommandSync(["convert", imagePath, writePath], TIFFConversionError, "Error converting {0} to TIFF".format(imagePath))
        return writePath
    else:
        raise TIFFImageError("{0} is not a valid image file".format(imagePath))

def convertImages(imagePaths, outputDir=None):
    '''
    Converts the images in the list of imagePaths to tiff format.
    Can optionaly specify the directory where the converted images will be saved, will default to putting them back into their original directories.
    If the path provided is not an image, it will be ignored.
    Returns a list of the paths to the new image files
    
    Exceptions:
    TiffConversionError: an error occurs during the conversion process
    '''
    convertedImages = []
    for imagePath in imagePaths:
        if isImage(imagePath):
            convertedImage = convertImage(imagePath, outputDir)
            convertedImages.append(convertedImage)
    return convertedImages
