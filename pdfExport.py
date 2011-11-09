import os
import shutil
import glob
import decapod_utilities as utils
import simplejson as json
import imghdr
from PIL import Image

#TODO: Consider adopting an asynchronous framework
# for asynchronous python 
from multiprocessing import Pool

BOOK_DIR = "${book}/capturedImages/"
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

class PDFGenerationError(Exception): pass

def createDir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def writeToFile(contents, writePath, writeMode="w"):
    f = open(writePath, writeMode)
    f.write(contents)
    f.close()
    
def isImage(filePath):
    return os.path.isfile(filePath) and imghdr.what(filePath) != None

def bookPagesToArray(pagesDir):
    allPages = []
    for fileName in os.listdir(pagesDir):
        filePath = os.path.join(pagesDir, fileName)
        
        if isImage(filePath): 
            allPages.append(filePath)
    return allPages

def convertPagesToTIFF(bookDir, tiffDir):
    tiff = ".tiff"
    for fileName in os.listdir(bookDir):
        name, ext = os.path.splitext(fileName)
        readPath = os.path.join(bookDir, fileName)
        writePath = os.path.join(tiffDir, name + tiff)
        
        if isImage(readPath):
            try:
                Image.open(readPath).save(writePath, "tiff")
            except IOError:
                raise PDFGenerationError

class PDFGenerator(object):
    
    status = {"status": EXPORT_NONE}
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
        self.bookDirPath = self.resources.filePath(BOOK_DIR)
        self.pdfDirPath = self.resources.filePath(PDF_DIR)
        self.tempDirPath = os.path.join(self.pdfDirPath, tempDir)
        self.tiffDirPath = os.path.join(self.pdfDirPath, tiffDir)
        self.statusFilePath = os.path.join(self.pdfDirPath, statusFileName)
        self.pdfPath = os.path.join(self.pdfDirPath, pdfName)
        
        self.setupExportFileStructure()
        
    def setupExportFileStructure(self):
        createDir(self.pdfDirPath)
            
        if not os.path.exists(self.statusFilePath):
            self.setStatus(EXPORT_NONE)
        else:
            statusFile = open(self.statusFilePath)
            self.status = json.load(statusFile)
            
    def clearExportDir(self):
        if os.path.exists(self.pdfDirPath):
            shutil.rmtree(self.pdfDirPath) 
        
    def writeToStatusFile(self):
        writeToFile(self.getStatus(), self.statusFilePath)
        
    def setStatus(self, status):
        st = self.status
        url = "url"
        st["status"] = status
        
        if status == EXPORT_COMPLETE:
            st[url] = self.pdfPath
        elif url in self.status:
            del self.status[url]
            
        self.writeToStatusFile()
    
    def getStatus(self):
        return json.dumps(self.status)
    
    def generatePDFFromPages(self, type="1"):
        genPDFCmd = [
            "decapod-genpdf.py",
            "-d",
            self.tempDirPath,
            "-p",
            self.pdfPath,
            "-v",
            "1",
            "-t",
            type
        ]
        genPDFCmd.extend(bookPagesToArray(self.tiffDirPath))
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
            createDir(self.tiffDirPath)
            convertPagesToTIFF(self.bookDirPath, self.tiffDirPath)
            self.generatePDFFromPages(type)
            self.setStatus(EXPORT_COMPLETE)
            return self.getStatus()
    
    #TODO: Raise specifid Exception if pdf generation in progress
    def deletePDF(self):
        if self.status["status"] == EXPORT_IN_PROGRESS:
            raise PDFGenerationError, "Export currently in progress, cannot delete the pdf until this process has finished"
        else:
            self.clearExportDir()
            self.setupExportFileStructure()

