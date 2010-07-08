import os
import shutil
import glob
import decapod_utilities as utils

pdfDir = "${generatedPDF}/"
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
            
    def convertPagesToTIFF(self, book, fullPDFPath):
        mogrifyCmd = [
            "mogrify",
            "-path",
            fullPDFPath,
            "-format",
            "tiff"
        ]
        for page in book:
            mogrifyCmd.append(self.resources.filePath(page["left"]))
            mogrifyCmd.append(self.resources.filePath(page["right"]))
            
        utils.invokeCommandSync(mogrifyCmd,
                                PDFGenerationError,
                                "Could not convert pages to TIFF format.")
    
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
    
    def generatePDFFromMultiPageTIFF(self, pdfName, multiPageTIFFName, fullPDFPath, tempDir):
        genPDFCmd = [
            "decapod-genpdf.py",
            "-d",
            os.path.join(fullPDFPath, tempDir),
            "-p",
            os.path.join(fullPDFPath, pdfName),
            "-v",
            "1",
            os.path.join(fullPDFPath, multiPageTIFFName)

        ]
        utils.invokeCommandSync(genPDFCmd,
                                PDFGenerationError,
                                "Could not generate a PDF version of the book.")
    
    def generate(self, book):
            fullPDFPath = self.setupExportDir()

            # TODO: Export should be asynchronous
            self.convertPagesToTIFF(book, fullPDFPath)
            self.createMultiPageTIFF(multiPageTIFFName, fullPDFPath)
            self.generatePDFFromMultiPageTIFF(pdfName, multiPageTIFFName, fullPDFPath, tempDir)

            return pdfDir + pdfName
