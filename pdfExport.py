import os
import shutil
import glob
import decapod_utilities as utils
import simplejson as json

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
tempDir = "genPDFTemp"

class PDFGenerationError(Exception): pass

def createDir(path):
    if not os.path.exists(path):
        os.mkdir(path)

class PDFGenerator(object):
    
    status = {"status": EXPORT_NONE}
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
        self.bookDirPath = self.resources.filePath(BOOK_DIR)
        self.pdfDirPath = self.resources.filePath(PDF_DIR)
        self.tempDirPath = os.path.join(self.pdfDirPath, tempDir)
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
            
    def writeToFile(self, contents, writePath, writeMode="w"):
        f = open(writePath, writeMode)
        f.write(contents)
        f.close()
        
    def writeToStatusFile(self):
        self.writeToFile(self.getStatus(), self.statusFilePath)
    
    def getStatus(self):
        return json.dumps(self.status)
        
    def clearExportDir(self):
        if os.path.exists(self.pdfDirPath):
            shutil.rmtree(self.pdfDirPath)   
            
    def bookPagesToArray(self):
        allPages = []
        for fileName in os.listdir(self.bookDirPath):
            filePath = os.path.join(self.bookDirPath, fileName)
            if os.path.isfile(filePath):
                allPages.append(filePath)
        return allPages
    
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
        genPDFCmd.extend(self.bookPagesToArray())
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
        
    def setStatus(self, status):
        st = self.status
        url = "url"
        st["status"] = status
        
        if status == EXPORT_COMPLETE:
            st[url] = self.pdfPath
        elif url in self.status:
            del self.status[url]
        
        self.writeToStatusFile()
    
    #TODO: Take in a the pages model and use it for determinig which pages are in a book
    #TODO: Raise specific Exception if pdf generation in progress
    #TODO: Raise an Exception if there are no pages in the book?
    def generate(self, type="1"):
        if self.status["status"] == EXPORT_IN_PROGRESS:
            raise PDFGenerationError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            self.setStatus(EXPORT_IN_PROGRESS)
            
            #TODO: This is just to test if the generation works, need to make this asynchronous
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

