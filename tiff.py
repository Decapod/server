import os
import decapod_utilities as utils
import imghdr
import zipfile

BOOK_DIR = "${library}/book/images/"
TIFF_DIR = BOOK_DIR + "tiff/"
TEMP_DIR = TIFF_DIR + "temp/"

# TODO: Move these values into configuration
statusFileName = "exportStatus.json"
tiffDir = "tiffTemp"

class TIFFConversionError(Exception): pass
class TIFFImageError(Exception): pass
class TIFFOutputPathError(Exception): pass

def convertImage(imagePath, outputDir=None):
    '''
    Converts the image at imagePath into a tiff image.
    Can optionaly specify the directory where to save the new file, will default to the same directory as the original file.
    Returns the path to the new image file.
    
    Exceptions:
    TIFFImageError: if the file at imagePath isn't a supported image format
    TIFFConversionError: an error occurs during the conversion process
    '''
    if utils.isImage(imagePath):
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
    TIFFConversionError: an error occurs during the conversion process
    '''
    convertedImages = []
    for imagePath in imagePaths:
        if utils.isImage(imagePath):
            convertedImage = convertImage(imagePath, outputDir)
            convertedImages.append(convertedImage)
    return convertedImages

def convertAndZipImages(imagePaths, outputPath, tempDir=None):
    '''
    Converts the images in the list of imagePaths to tiff format.
    Must specify the output path, including the file name, for the zip file to be saved.
    If the image path provided is not an image, it will be ignored.
    Can optionally specify a temp derictory for use during conversion, 
    it will default to creating a temp directory in the current working directory.
    Note that in all cases, the temp directory will be removed after completion.
    Returns a path to the zip file containing the converted images.
    If no valid images were provided, None is returned
    
    Exceptions:
    TIFFConversionError: an error occurs during the conversion process
    TIFFOutputPathError: the output path is malformed (e.g. path to a directory)
    '''
    zipPath = outputPath
    currentDir = os.getcwd()
    temp = tempDir if tempDir != None else os.path.join(os.getcwd(), "temp")
    utils.makeDirs(tempDir)
    converted = convertImages(imagePaths, temp)
    os.chdir(tempDir) # Need to change to the tempDir where the images are so that the zip file won't contain any directory structure
    if len(converted) > 0:
        try:
            zip = zipfile.ZipFile(outputPath, mode="a")
        except IOError:
            raise TIFFOutputPathError("{0} is not a valid path".format(outputPath))
        for imagePath in converted:
            imageFile = os.path.split(imagePath)[1] # extacts the filename from the path
            zip.write(imageFile)
        zip.close()
    else:
        # Return None when there are no valid image paths
        zipPath = None
    
    os.chdir(currentDir)
    utils.rmTree(tempDir)
    return zipPath
