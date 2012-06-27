import os
import decapod_utilities as utils
import resourcesource
from image import batchConvert
from status import status

BOOK_DIR = "${library}/book/"
IMAGES_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
PDF_DIR = os.path.join(EXPORT_DIR, "pdf/")

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_READY = "ready"

# TODO: Move these values into configuration
pdfName = "Decapod.pdf"
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

class PDFGenerationError(Exception): pass

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

class PDFGenerator(object):
    
    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.bookDirPath = self.rs.path(IMAGES_DIR)
        self.pdfDirPath = self.rs.path(PDF_DIR)
        self.tempDirPath = os.path.join(self.pdfDirPath, tempDir)
        self.tiffDirPath = os.path.join(self.pdfDirPath, tiffDir)
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
        '''
        return str(self.status)
    
    def generatePDFFromPages(self, options={"-t": "1"}):
        '''
        Will trigger the pdf generation using the images at the defined by self.tiffPages
        '''
        genPDFCmd = assembleGenPDFCommand(self.tempDirPath, self.pdfPath, self.tiffPages, options)
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    #TODO: Take in a the pages model and use it for determinig which pages are in a book
    #TODO: Raise specific Exception if pdf generation in progress
    #TODO: Raise an Exception if there are no pages in the book?
    def generate(self, options={"type": "1"}):
        '''
        Generates the pdf export.
        If an export is already in progress, an exception is raised
        '''
        if self.status.inState(EXPORT_IN_PROGRESS):
            raise PDFGenerationError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            utils.makeDirs(self.tiffDirPath)
            self.pages = utils.imageDirToList(self.bookDirPath);
            self.tiffPages = batchConvert(self.pages, "tiff", self.tiffDirPath)
            self.generatePDFFromPages(utils.rekey(options, KEY_MAP))
            self.setStatus(EXPORT_COMPLETE, includeURL=True)
            return self.getStatus()
    
    #TODO: Raise specifid Exception if pdf generation in progress
    def deletePDF(self):
        '''
        Removes the export artifacts.
        '''
        if self.status.inState(EXPORT_IN_PROGRESS):
            raise PDFGenerationError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            utils.rmTree(self.pdfDirPath)
            self.setupExportFileStructure()
