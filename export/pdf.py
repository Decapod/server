import os
import sys

from image import batchConvert
sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils
import resourcesource
from status import Status
from store import FSStore

BOOK_DIR = "${library}/book/"
IMAGES_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
PDF_DIR = os.path.join(EXPORT_DIR, "pdf/")

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_READY = "ready"
EXPORT_ERROR = "error"

# TODO: Move these values into configuration
pdfName = "Decapod.pdf"
pdfGenerationStatusFileName = "Decapod.json"
statusFileName = "exportStatus.json"
tiffDir = "tiffTemp"
tempDir = "genPDFTemp"

# maps the query paramaters to the format needed by genpdf
KEY_MAP = {
    "type": "-t",           
    "w": "--width", 
    "width": "--width", 
    "h": "--height", 
    "height": "--height", 
    "dpi": "-r", # should be -dpi, but set to -r due to DECA-294
# removing colour options due to DECA-295
#    "c": "-c",
#    "color": "-c",
#    "colour": "-c",
    "bit": "--bit", # should be -bit, but set to --bit due to DECA-294
}

# Exception classes
class PDFGenerationError(Exception): pass
class PDFGenerationInProgressError(Exception): pass
class PageImagesNotFoundError(Exception): pass

def assembleGenPDFCommand(tempDirPath, pdfPath, pages, options={"-t": "1"}):
    '''
    compiles the command line call to run genpdf.
    '''
    genPDFCmd = [
        "decapod-genpdf.py",
        "-d",
        tempDirPath,
        "-p",
        pdfPath,
        "-v",
        "1"
    ]
    
    flags = utils.translate.weave(options)
    genPDFCmd.extend(flags)
    genPDFCmd.extend(pages)
    return genPDFCmd

def getGENPDFStage(genPDFStatusFile):
    '''
    Returns the value of the "stage" key from the genPDF progress file or None if it is not present.
    '''
    stage = None
    
    if os.path.exists(genPDFStatusFile):
        genPDFStatus = utils.io.loadJSONFile(genPDFStatusFile)
        stage = genPDFStatus.get("stage")
        
    return stage

class PDFGenerator(object):
    
    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.bookDirPath = self.rs.path(IMAGES_DIR)
        self.pdfDirPath = self.rs.path(PDF_DIR)
        self.tempDirPath = os.path.join(self.pdfDirPath, tempDir)
        self.tiffDirPath = os.path.join(self.pdfDirPath, tiffDir)
        self.pdfGenerationStatusFilePath = os.path.join(self.pdfDirPath, pdfGenerationStatusFileName)
        self.statusFilePath = os.path.join(self.pdfDirPath, statusFileName)
        self.pdfPath = os.path.join(self.pdfDirPath, pdfName)
        self.pages = None
        self.tiffPages = None
        
        self.setupExportFileStructure()
        self.status = Status(FSStore(self.statusFilePath), {"status": EXPORT_READY})  

    def setupExportFileStructure(self):
        '''
        Sets up the directory structure and initializes the status
        '''
        utils.io.makeDirs(self.pdfDirPath)
        
    def setStatus(self, state, includeURL=False):
        '''
        Updates the status file with the new state. 
        If inlcudeURL is set to true, the url properly will be added with the path to the export
        '''
        self.status.update("status", state)
        
        if includeURL:
            virtualPath = os.path.join(PDF_DIR, os.path.split(self.pdfPath)[1])
            self.status.update("url", self.rs.url(virtualPath))
        else:
            self.status.remove("url")

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):
        '''
        If the export is in progress, it will check the genpdf progress file to add stage information to the status.
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            genPDFStage = getGENPDFStage(self.pdfGenerationStatusFilePath)
            self.status.update("stage", genPDFStage if genPDFStage is not None else "")
        else:
            self.status.remove("stage")
        
        return self.status.model
    
    def generatePDFFromPages(self, options={"-t": "1"}):
        '''
        Will trigger the pdf generation using the images at the defined by self.tiffPages
        
        Exceptions
        ==========
        PDFGenerationError: if there is error during the pdf creation process
        '''
        genPDFCmd = assembleGenPDFCommand(self.tempDirPath, self.pdfPath, self.tiffPages, options)
        utils.io.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    #TODO: Take in a the pages model and use it for determinig which pages are in a book
    def generate(self, options={"type": "1"}):
        '''
        Generates the pdf export.
        If an exception is raised from the genPDF subprocess the status will be set to EXPORT_ERROR
        
        Exceptions
        ==========
        PDFGenerationInProgressError: if an export is currently in progress
        PageImagesNotFoundError: if no page images are provided for the pdf generation
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise PDFGenerationInProgressError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            utils.io.makeDirs(self.tiffDirPath)
            self.pages = utils.image.imageListFromDir(self.bookDirPath, sortKey=os.path.getmtime);
            if len(self.pages) is 0:
                self.setStatus(EXPORT_ERROR)
                raise PageImagesNotFoundError("No page images found, cannot generate a pdf")
            try:
                self.tiffPages = batchConvert(self.pages, "tiff", self.tiffDirPath)
                self.generatePDFFromPages(utils.translate.map(options, KEY_MAP))
            except:
                self.setStatus(EXPORT_ERROR)
                raise
            self.setStatus(EXPORT_COMPLETE, includeURL=True)
            return self.getStatus()
    
    def deletePDF(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        PDFGenerationInProgressError: if an export is currently in progress
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise PDFGenerationInProgressError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            utils.io.rmTree(self.pdfDirPath)
            self.setupExportFileStructure()
            self.setStatus(EXPORT_READY)
