import sys
import os
import unittest
import shutil
import simplejson as json

import testutils
sys.path.append(os.path.abspath('..'))
import pdf
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIBRARY_PATH = os.path.join(DATA_DIR, "library/")
BOOK_DIR = os.path.join(LIBRARY_PATH, "book/")
IMG_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
PDF_DIR = os.path.join(EXPORT_DIR, "pdf/")
STATUS_FILE = os.path.join(PDF_DIR, "exportStatus.json")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

class TestPDFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        utils.rmTree(BOOK_DIR)
        
    def test_01_assembleGenPDFCommand(self):
        tempDirPath = "../temp"
        pdfPath = "../Decapod.pdf"
        pages = ["../images/pageOne.jpg", "../images/pageTwo.jpg"]
        expectedCMD = "decapod-genpdf.py -d {0} -p {1} -v 1 -t 1 {2} {3}".format(tempDirPath, pdfPath, pages[0], pages[1])
        self.assertEquals(expectedCMD.split(), pdf.assembleGenPDFCommand(tempDirPath, pdfPath, pages))
        
    def test_02_assembleGenPDFCommand_type(self):
        tempDirPath = "../temp"
        pdfPath = "../Decapod.pdf"
        type = 2
        pages = ["../images/pageOne.jpg", "../images/pageTwo.jpg"]
        expectedCMD = "decapod-genpdf.py -d {0} -p {1} -v 1 -t {2} {3} {4}".format(tempDirPath, pdfPath, type, pages[0], pages[1])
        self.assertEquals(expectedCMD.split(), pdf.assembleGenPDFCommand(tempDirPath, pdfPath, pages, type))

class TestPDFGenerator(unittest.TestCase):
    book = None
    mockRS = testutils.mockResourceSource({"/library": {"path": LIBRARY_PATH, "url": "/library"}})
    status_complete = '{"status": "complete", "url": "/library/book/export/pdf/Decapod.pdf"}'
    status_inProgress = '{"status": "in progress"}'
    status_ready = '{"status": "ready"}'
    
    def setUp(self):
        utils.makeDirs(IMG_DIR)
        
    def tearDown(self):
        utils.rmTree(BOOK_DIR)
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        file = open(statusFile)
        read = file.read()
        file.close()
        self.assertEquals(status, read)
    
    def assertInit(self, PDFGenerator, testStatus):
        self.assertEquals(IMG_DIR, PDFGenerator.bookDirPath)
        self.assertEquals(PDF_DIR, PDFGenerator.pdfDirPath)
        self.assertEquals(os.path.join(PDF_DIR, "genPDFTemp"), PDFGenerator.tempDirPath)
        self.assertEquals(os.path.join(PDF_DIR, "tiffTemp"), PDFGenerator.tiffDirPath)
        self.assertEquals(STATUS_FILE, PDFGenerator.statusFilePath)
        self.assertEquals(os.path.join(PDF_DIR, "Decapod.pdf"), PDFGenerator.pdfPath)
        self.assertEquals(None, PDFGenerator.pages)
        self.assertEquals(None, PDFGenerator.tiffPages)
        self.assertStatusFile(testStatus)
        self.assertEquals(testStatus, json.dumps(PDFGenerator.status.status))
        self.assertTrue(os.path.exists(PDF_DIR), "The pdf directory ({0}) should exist".format(PDF_DIR))
            
    def test_01_init(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertInit(pdfGen, self.status_ready)
            
    def test_02_init_statusFile(self):
        utils.makeDirs(PDF_DIR)
        file = open(STATUS_FILE, "w")
        file.write(self.status_inProgress)
        file.close()
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertInit(pdfGen, self.status_inProgress)
    
    def test_04_setStatus(self):
        st = "test"
        status = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(st)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status.status))
        
    def test_05_setStatus_removeURL(self):
        st = "test"
        newStatus = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.status.status = json.loads(self.status_complete)
        pdfGen.setStatus(st)
        self.assertStatusFile(newStatus)
        self.assertEquals(newStatus, json.dumps(pdfGen.status.status))
        
    def test_06_setStatus_addURL(self):
        st = "complete"
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(st, includeURL=True)
        self.assertStatusFile(self.status_complete)
        self.assertEquals(self.status_complete, json.dumps(pdfGen.status.status))
        
    def test_07_getStatus(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        status = pdfGen.getStatus()
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status.status))
    
    def test_08_generatePDFFromPages_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.tiffPages = []
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generatePDFFromPages)
        
    def test_09_generate(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        utils.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = pdfGen.generate()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
        self.assertStatusFile(self.status_complete)
        self.assertEquals(self.status_complete, json.dumps(pdfGen.status.status))
        self.assertEquals(self.status_complete, returnedStatus)
        
    def test_10_generate_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generate)
        
    def test_11_deletePDF(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        utils.makeDirs(PDF_DIR)
        shutil.copy(os.path.join(DATA_DIR, "pdf/Decapod.pdf"), PDF_DIR)
        pdfGen.setStatus("complete")
        pdfGen.deletePDF()
        self.assertInit(pdfGen, self.status_ready)
        self.assertFalse(os.path.exists(os.path.join(PDF_DIR, "Decapod.pdf")), "The export pdf should not exist")
        
    def test_12_deletePDF_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus("in progress")
        self.assertRaises(pdf.PDFGenerationError, pdfGen.deletePDF)
        
if __name__ == '__main__':
    unittest.main()
