import os
import sys
import imghdr
import zipfile

from string import Template
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import resourcesource
from store import FSStore
from status import Status
import utils

#constants for paths
BOOK_DIR = "${library}/book/"
IMAGES_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
IMG_DIR = os.path.join(EXPORT_DIR, "image/")
TEMP_DIR = os.path.join(IMG_DIR, "temp/")
STATUS_FILE = os.path.join(IMG_DIR, "exportStatus.json")

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_READY = "ready"
EXPORT_ERROR = "error"

#Exception classes
class ConversionError(Exception): pass
class ImageError(Exception): pass
class OutputPathError(Exception): pass
class ExportInProgressError(Exception): pass
class ImagesNotFoundError(Exception): pass

def convert(imagePath, format, outputDir=None, name=None):
    '''
    Converts the image at imagePath into the specified image format
    Can optionaly specify the directory where to save the new file, will default to the same directory as the original file.
    Can optionaly specify a new name for the file, will default to using the same name as the original file.
    If the format is invalid, it will convert it to jpeg
    Returns the path to the new image file.
    
    Exceptions
    ==========
    ImageError: if the file at imagePath isn't a supported image format
    ConversionError: an error occurs during the conversion process
    '''
    if utils.image.isImage(imagePath):
        ext = format[1:] if format.startswith(".") else format
        origDir, fileName = os.path.split(imagePath)
        newName = name if name else os.path.splitext(fileName)[0]
        writeDir = outputDir if outputDir else origDir
        
        writePath = os.path.join(writeDir, "{0}.{1}".format(newName, ext))
        utils.io.invokeCommandSync(["convert", imagePath, writePath], ConversionError, "Error converting {0} to '{1}' format".format(imagePath, format))
        return writePath
    else:
        raise ImageError("{0} is not a valid image file".format(imagePath))

def batchConvert(imagePaths, format, outputDir=None, nameTemplate=None):
    '''
    Converts the image at imagePath into the specified image format
    Can optionaly specify the directory where the converted images will be saved, will default to putting them back into their original directories.
    Can optionaly specify a name tempalte to rename the converted images with. The template should include the "$index" token. By default the files will retain their original name. 
    If the path provided is not an image, it will be ignored.
    If the format is invalid, it will convert it to jpeg
    Returns a list of the paths to the new image files
    
    Exceptions
    ==========
    ConversionError: an error occurs during the conversion process
    '''
    convertedImages = []
    index = 1;
    digits = len(str(len(imagePaths))) #retrieves the number of digits in the length of imagePaths
    for imagePath in imagePaths:
        if utils.image.isImage(imagePath):
            count = str(index).zfill(digits) # converts the index to start from 1 instead of 0. and pads it with leading 0s if needed.
            name = Template(nameTemplate).safe_substitute(index=count) if nameTemplate else None
            convertedImage = convert(imagePath, format, outputDir, name)
            convertedImages.append(convertedImage)
            index += 1;
    return convertedImages

def archiveConvert(imagePaths, format, archivePath, tempDir=None, nameTemplate=None):
    '''
    Converts the images in the list of imagePaths to tiff format.
    Must specify the output path, including the file name, for the zip file to be saved.
    If the image path provided is not an image, it will be ignored.
    Can optionally specify a temp derictory for use during conversion, 
    it will default to creating a temp directory in the current working directory.
    Can optionaly specify a name tempalte to rename the converted images with. The template 
    should include the "$index" token. By default the files will retain their original name.
    Note that in all cases, the temp directory will be removed after completion.
    Returns a path to the zip file containing the converted images.
    If no valid images were provided, None is returned
    
    Exceptions
    ==========
    ConversionError: an error occurs during the conversion process
    OutputPathError: the output path is malformed (e.g. path to a directory)
    '''
    currentDir = os.getcwd()
    temp = tempDir if tempDir else os.path.join(os.getcwd(), "temp")
    utils.io.makeDirs(temp)
    converted = batchConvert(imagePaths, format, temp, nameTemplate)
    if len(converted) > 0:
        try:
            zip = zipfile.ZipFile(archivePath, mode="a")
        except IOError:
            utils.io.rmTree(tempDir)
            raise OutputPathError("{0} is not a valid path".format(archivePath))
        os.chdir(tempDir) # Need to change to the tempDir where the images are so that the zip file won't contain any directory structure
        for imagePath in converted:
            imageFile = os.path.basename(imagePath)
            zip.write(imageFile)
        zip.close()
        os.chdir(currentDir)
        utils.io.rmTree(temp)
        return archivePath
    else:
        # Return None when there are no valid image paths
        utils.io.rmTree(temp)
        return None
    
class ImageExporter(object):
    
    def __init__(self, resourcesource=resourcesource, archiveName="Decapod.zip", nameTemplate=None):
        '''
        Creates the ImageExporter instance.
        Can optionaly specify an archiveName, including extension, for the exported file package.
        Can optionaly specify a name tempalte to rename the converted images with. The template should include the "$index" token. By default the files will retain their original name.
        '''
        self.rs = resourcesource
        self.bookDirPath = self.rs.path(IMAGES_DIR)
        self.imgDirPath = self.rs.path(IMG_DIR)
        self.tempDirPath = self.rs.path(TEMP_DIR)
        self.statusFilePath = self.rs.path(STATUS_FILE)
        self.archivePath = os.path.join(self.imgDirPath, archiveName)
        self.nameTemplate = nameTemplate
        
        self.setupExportFileStructure()
        self.status = Status(FSStore(self.statusFilePath), {"status": EXPORT_READY})      
        
    def setupExportFileStructure(self):
        '''
        Sets up the directory structure
        '''
        utils.io.makeDirs(self.imgDirPath)
        utils.io.makeDirs(self.tempDirPath)
        
    def setStatus(self, state, includeURL=False):
        '''
        Updates the status file with the new state. 
        If inlcudeURL is set to true, the url properly will be added with the path to the export
        '''
        self.status.update("status", state)
        
        if includeURL:
            virtualPath = os.path.join(IMG_DIR, os.path.split(self.archivePath)[1])
            self.status.update("url", self.rs.url(virtualPath))
        else:
            self.status.remove("url")

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):
        return self.status.model
    
    def export(self, format):
        '''
        Will trigger the export of the images into a zip file containing the images converted into the specified format
        If an exception is raised from the archiveConvert call the status will be set to EXPORT_ERROR
        
        Exceptions
        ==========
        ExportInProgressError: if an export is currently in progress
        ImagesNotFoundError: if no images are provided for the export
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise ExportInProgressError, "Export currently in progress, cannot generated another export until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            self.imagePaths = utils.image.imageListFromDir(self.bookDirPath, sortKey=os.path.getmtime);
            if len(self.imagePaths) is 0:
                self.setStatus(EXPORT_ERROR)
                raise ImagesNotFoundError("No images found, nothing to export")
            try:
                archiveConvert(self.imagePaths, format, self.archivePath, self.tempDirPath, self.nameTemplate)
            except:
                self.setStatus(EXPORT_ERROR)
                raise
            self.setStatus(EXPORT_COMPLETE, includeURL=True)
            return self.getStatus()

    def deleteExport(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        ExportInProgressError: if an export is currently in progress
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise ExportInProgressError, "Export currently in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.imgDirPath)
            self.setupExportFileStructure()
            self.setStatus(EXPORT_READY)
