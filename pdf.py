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
EXPORT_NONE = "none"

# TODO: Move these values into configuration
pdfName = "Decapod.pdf"
statusFileName = "exportStatus.json"
tiffDir = "tiffTemp"
tempDir = "genPDFTemp"

class PDFGenerationError(Exception): pass

def assembleGenPDFCommand(tempDirPath, pdfPath, pages, type="1"):
    genPDFCmd = [
        "decapod-genpdf.py",
        "-d",
        tempDirPath,
        "-p",
        pdfPath,
        "-v",
        "1",
        "-t",
        str(type)
    ]
    genPDFCmd.extend(pages)
    return genPDFCmd

class PDFGenerator(object):
    
    status = {"status": EXPORT_NONE}
    
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
        utils.makeDirs(self.pdfDirPath)
        self.status = status(self.statusFilePath)
        if not self.status.status.has_key("status"):
            self.setStatus(EXPORT_NONE)
    
    def setStatus(self, state, includeURL=False):
        newStatus = {"status": state}
        
        if (includeURL):
            virtualPath = PDF_DIR + os.path.split(self.pdfPath)[1]
            newStatus["url"] = self.rs.url(virtualPath)
            
        self.status.set(newStatus)
        
    def isState(self, state):
        return self.status.status["status"] == state

    def getStatus(self):
        return self.status.getStatusString()
    
    def generatePDFFromPages(self, type="1"):
        genPDFCmd = assembleGenPDFCommand(self.tempDirPath, self.pdfPath, self.tiffPages, type)
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    #TODO: Take in a the pages model and use it for determinig which pages are in a book
    #TODO: Raise specific Exception if pdf generation in progress
    #TODO: Raise an Exception if there are no pages in the book?
    def generate(self, type="1"):
        if self.isState(EXPORT_IN_PROGRESS):
            raise PDFGenerationError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            utils.makeDirs(self.tiffDirPath)
            self.pages = utils.imageDirToList(self.bookDirPath);
            self.tiffPages = batchConvert(self.pages, "tiff", self.tiffDirPath)
            self.generatePDFFromPages(type)
            self.setStatus(EXPORT_COMPLETE, includeURL=True)
            return self.getStatus()
    
    #TODO: Raise specifid Exception if pdf generation in progress
    def deletePDF(self):
        if self.isState(EXPORT_IN_PROGRESS):
            raise PDFGenerationError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            utils.rmTree(self.pdfDirPath)
            self.setupExportFileStructure()
