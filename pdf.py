import os
import decapod_utilities as utils
import simplejson as json
import imghdr
from PIL import Image
import resourcesource
from image import batchConvert

BOOK_DIR = "${library}/book/"
IMAGES_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
PDF_DIR = os.path.join(EXPORT_DIR, "pdf/")

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

class PDFGenerationError(Exception): pass

def bookPagesToArray(pagesDir):
    allPages = []
    for fileName in os.listdir(pagesDir):
        filePath = os.path.join(pagesDir, fileName)
        
        if utils.isImage(filePath): 
            allPages.append(filePath)
    # sorting needed to keep pages in order
    return sorted(allPages, key = os.path.getmtime)

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
            
        if not os.path.exists(self.statusFilePath):
            self.setStatus(EXPORT_NONE)
        else:
            statusFile = open(self.statusFilePath)
            self.status = json.load(statusFile)
        
    def writeToStatusFile(self):
        utils.writeToFile(self.getStatus(), self.statusFilePath)
        
    def setStatus(self, status):
        st = self.status
        url = "url"
        st["status"] = status
        
        if status == EXPORT_COMPLETE:
            virtualPath = PDF_DIR + os.path.split(self.pdfPath)[1]
            st[url] = self.rs.url(virtualPath)
        elif url in self.status:
            del self.status[url]
            
        self.writeToStatusFile()
    
    def getStatus(self):
        return json.dumps(self.status)
    
    def generatePDFFromPages(self, type="1"):
        genPDFCmd = assembleGenPDFCommand(self.tempDirPath, self.pdfPath, self.tiffPages, type)
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    #TODO: Take in a the pages model and use it for determinig which pages are in a book
    #TODO: Raise specific Exception if pdf generation in progress
    #TODO: Raise an Exception if there are no pages in the book?
    def generate(self, type="1"):
        if self.status["status"] == EXPORT_IN_PROGRESS:
            raise PDFGenerationError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            utils.makeDirs(self.tiffDirPath)
            self.pages = bookPagesToArray(self.bookDirPath);
            self.tiffPages = batchConvert(self.pages, "tiff", self.tiffDirPath)
            self.generatePDFFromPages(type)
            self.setStatus(EXPORT_COMPLETE)
            return self.getStatus()
    
    #TODO: Raise specifid Exception if pdf generation in progress
    def deletePDF(self):
        if self.status["status"] == EXPORT_IN_PROGRESS:
            raise PDFGenerationError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            utils.rmTree(self.pdfDirPath)
            self.setupExportFileStructure()

