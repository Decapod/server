import os
import shutil
import glob
import decapod_utilities as utils

pdfDir = "${book}/pdf/"
# TODO: Move these values into configuration
multiPageTIFFName = "Decapod-multipage.tiff"
pdfName = "Decapod.pdf"
tempDir = "genPDFTemp"

class PDFGenerationError(Exception): pass

class PDFGenerator:
    
    resources = None
    
    def __init__(self, resourceSource):
        self.resources = resourceSource
    
    def setupExportDir(self):
        # Clean up any previously-exported PDFs before exporting a new one.
        fullPDFPath = self.resources.filePath(pdfDir)
        if os.path.exists(fullPDFPath):
            shutil.rmtree(fullPDFPath)        
        os.mkdir(fullPDFPath)
        
        return fullPDFPath
            
    def bookPagesToArray(self, book):
        allPages = []
        for page in book:
            allPages.append(self.resources.filePath(page["left"]))
            allPages.append(self.resources.filePath(page["right"]))
        return allPages
            
    # TODO: It appears we don't need this process any more. Ditch it?
    def convertPagesToTIFF(self, book, fullPDFPath):
        mogrifyCmd = [
            "mogrify",
            "-path",
            fullPDFPath,
            "-format",
            "tiff"
        ]
        mogrifyCmd.extend(self.bookPagesToArray(book))
            
        utils.invokeCommandSync(mogrifyCmd,
                                PDFGenerationError,
                                "Could not convert pages to TIFF format.")
    
    # TODO: It appears we don't need this process any more. Ditch it?
    def createMultiPageTIFF(self, tiffName, fullPDFPath):
        inputTIFFs = glob.glob(os.path.join(fullPDFPath, "*.tiff"))
        multiPageTIFFCmd = [
            "tiffcp"
        ]
        multiPageTIFFCmd.extend(inputTIFFs)
        multiPageTIFFCmd.append(os.path.join(fullPDFPath, tiffName))
        
        utils.invokeCommandSync(multiPageTIFFCmd,
                                PDFGenerationError,
                                "Could not generate a multipage TIFF file.")
    
    def generatePDFFromBook(self, book, pdfPath, tempPath):
        genPDFCmd = [
            "decapod-genpdf.py",
            "-d",
            tempPath,
            "-p",
            pdfPath,
            "-v",
            "1"
        ]
        genPDFCmd.extend(self.bookPagesToArray(book))
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    def generate(self, book):
            fullPDFPath = self.setupExportDir()
            pdfPath = os.path.join(fullPDFPath, pdfName)
            tempPath = os.path.join(fullPDFPath, tempDir)
            
            # TODO: Export should be asynchronous
            self.generatePDFFromBook(book, pdfPath, tempPath)

            return pdfDir + pdfName
