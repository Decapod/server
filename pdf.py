import os
import decapod_utilities as utils
import resourcesource
from image import batchConvert
from status import status, loadJSONFile

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
    "w": "-w", 
    "width": "-w", 
    "h": "-h", 
    "height": "-h", 
    "dpi": "-dpi",
    "c": "-c",
    "color": "-c",
    "colour": "-c",
    "bit": "-bit",
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
    
    flags = utils.dictToFlagList(options)
    genPDFCmd.extend(flags)
    genPDFCmd.extend(pages)
    return genPDFCmd

def getGENPDFStage(genPDFStatusFile):
    '''
    Returns the value of the "stage" key from the genPDF progress file.
    If either the file or the stage key is not present, a default dictionary is returned with the stage an empty string ""
    '''
    stage = {"stage": ""}
    
    if os.path.exists(genPDFStatusFile):
        genPDFStatus = loadJSONFile(genPDFStatusFile)
        if "stage" in genPDFStatus:
            stage["stage"] = genPDFStatus["stage"]
        
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

    def setupExportFileStructure(self):
        '''
        Sets up the directory structure and initializes the status
        '''
        utils.makeDirs(self.pdfDirPath)
        self.status = status(self.statusFilePath, EXPORT_READY)
    
    def setStatus(self, state, includeURL=False):
        '''
        Updates the status file with the new state. 
        If inlcudeURL is set to true, the url properly will be added with the path to the export
        '''
        newStatus = {"status": state}
        
        if (includeURL):
            virtualPath = PDF_DIR + os.path.split(self.pdfPath)[1]
            newStatus["url"] = self.rs.url(virtualPath)
            
        self.status.set(newStatus)

    def getStatus(self):
        '''
        Returns a string representation of the status
        
        If the export is in progress, it will check the genpdf progress file to add stage information to the status.
        '''
        if self.status.inState(EXPORT_IN_PROGRESS):
            self.status.update(getGENPDFStage(self.pdfGenerationStatusFilePath))
        
        return str(self.status)
    
    def generatePDFFromPages(self, options={"-t": "1"}):
        '''
        Will trigger the pdf generation using the images at the defined by self.tiffPages
        
        Exceptions
        ==========
        PDFGenerationError: if there is error during the pdf creation process
        '''
        genPDFCmd = assembleGenPDFCommand(self.tempDirPath, self.pdfPath, self.tiffPages, options)
        utils.invokeCommandSync(genPDFCmd,
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
        if self.status.inState(EXPORT_IN_PROGRESS):
            raise PDFGenerationInProgressError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            utils.makeDirs(self.tiffDirPath)
            self.pages = utils.imageDirToList(self.bookDirPath);
            if len(self.pages) is 0:
                raise PageImagesNotFoundError("No page images found, cannot generate a pdf")
            self.tiffPages = batchConvert(self.pages, "tiff", self.tiffDirPath)
            try:
                self.generatePDFFromPages(utils.rekey(options, KEY_MAP))
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
        if self.status.inState(EXPORT_IN_PROGRESS):
            raise PDFGenerationInProgressError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            utils.rmTree(self.pdfDirPath)
            self.setupExportFileStructure()
