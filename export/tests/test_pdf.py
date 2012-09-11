import sys
import os
import unittest
import shutil
import simplejson as json

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
import testutils
import pdf
from utils import io

DATA_DIR = os.path.abspath("data/")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LIBRARY_PATH = os.path.join(DATA_DIR, "library/")
BOOK_DIR = os.path.join(LIBRARY_PATH, "book/")
IMG_DIR = os.path.join(BOOK_DIR, "images/")
EXPORT_DIR = os.path.join(BOOK_DIR, "export/")
PDF_DIR = os.path.join(EXPORT_DIR, "pdf/")
STATUS_FILE = os.path.join(PDF_DIR, "exportStatus.json")
GENPDF_STATUS_FILE = os.path.join(PDF_DIR, "Decapod.json")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

class TestPDFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        io.makeDirs(TEST_DIR)
            
    def tearDown(self):
        io.rmTree(TEST_DIR)
        io.rmTree(BOOK_DIR)
        
    def test_01_assembleGenPDFCommand(self):
        tempDirPath = "../temp"
        pdfPath = "../Decapod.pdf"
        pages = ["../images/pageOne.jpg", "../images/pageTwo.jpg"]
        expectedCMD = "decapod-genpdf.py -d {0} -p {1} -v 1 -t 1 {2} {3}".format(tempDirPath, pdfPath, pages[0], pages[1])
        self.assertEquals(expectedCMD.split(), pdf.assembleGenPDFCommand(tempDirPath, pdfPath, pages))
        
    def test_02_assembleGenPDFCommand_options(self):
        tempDirPath = "../temp"
        pdfPath = "../Decapod.pdf"
        options = {"-t": "2", "-dpi": "300"}
        pages = ["../images/pageOne.jpg", "../images/pageTwo.jpg"]
        expectedCMD = "decapod-genpdf.py -d {0} -p {1} -v 1 -t {2} -dpi {3} {4} {5}".format(tempDirPath, pdfPath, options["-t"], options["-dpi"], pages[0], pages[1])
        self.assertListEqual(expectedCMD.split(), pdf.assembleGenPDFCommand(tempDirPath, pdfPath, pages, options))
        
    def test_03_getGENPDFStage(self):
        io.makeDirs(PDF_DIR)
        testStatus = '{"stage": "generating", "running": "on"}'
        expected = {"stage": "generating"}
        io.writeToFile(testStatus, GENPDF_STATUS_FILE)
        stageInfo = pdf.getGENPDFStage(GENPDF_STATUS_FILE)
        self.assertDictEqual(expected, stageInfo)
        
    def test_04_getGENPDFStage_noStageKey(self):
        io.makeDirs(PDF_DIR)
        testStatus = '{"running": "on"}'
        expected = {"stage": ""}
        io.writeToFile(testStatus, GENPDF_STATUS_FILE)
        stageInfo = pdf.getGENPDFStage(GENPDF_STATUS_FILE)
        self.assertDictEqual(expected, stageInfo)
        
    def test_05_getGENPDFStage_noStatusFile(self):
        io.makeDirs(PDF_DIR)
        expected = {"stage": ""}
        stageInfo = pdf.getGENPDFStage(GENPDF_STATUS_FILE)
        self.assertDictEqual(expected, stageInfo)

#TODO: test that the status is set to "error" when genPDF fails
class TestPDFGenerator(unittest.TestCase):
    book = None
    mockRS = testutils.mockResourceSource({"/library": {"path": LIBRARY_PATH, "url": "/library"}})
    status_complete = '{"status": "complete", "url": "/library/book/export/pdf/Decapod.pdf"}'
    status_inProgress = '{"status": "in progress"}'
    status_ready = '{"status": "ready"}'
    
    def setUp(self):
        io.makeDirs(IMG_DIR)
        
    def tearDown(self):
        io.rmTree(BOOK_DIR)
    
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
        io.makeDirs(PDF_DIR)
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
        
    def test_08_getStatus_inProgress(self):
        io.makeDirs(PDF_DIR)
        testStatus = {"stage": "generating"}
        io.writeToFile(json.dumps(testStatus), GENPDF_STATUS_FILE)
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(pdf.EXPORT_IN_PROGRESS)
        status = pdfGen.getStatus()
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status.status))
        self.assertEquals(testStatus["stage"], pdfGen.status.status["stage"])
    
    def test_09_generatePDFFromPages_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.tiffPages = []
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generatePDFFromPages)
        
    def test_10_generate(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        io.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = pdfGen.generate()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
        self.assertStatusFile(self.status_complete)
        self.assertEquals(self.status_complete, json.dumps(pdfGen.status.status))
        self.assertEquals(self.status_complete, returnedStatus)
        
    def test_11_generate_options(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        io.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = pdfGen.generate({"type": "2"})
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
        self.assertStatusFile(self.status_complete)
        self.assertEquals(self.status_complete, json.dumps(pdfGen.status.status))
        self.assertEquals(self.status_complete, returnedStatus)
        
    def test_12_generate_exception_noPageImages(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertRaises(pdf.PageImagesNotFoundError, pdfGen.generate)
        
    def test_13_generate_exception_inProgress(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(pdf.EXPORT_IN_PROGRESS)
        self.assertRaises(pdf.PDFGenerationInProgressError, pdfGen.generate)
    
    def test_14_deletePDF(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        io.makeDirs(PDF_DIR)
        shutil.copy(os.path.join(DATA_DIR, "pdf/Decapod.pdf"), PDF_DIR)
        pdfGen.setStatus("complete")
        pdfGen.deletePDF()
        self.assertInit(pdfGen, self.status_ready)
        self.assertFalse(os.path.exists(os.path.join(PDF_DIR, "Decapod.pdf")), "The export pdf should not exist")
        
    def test_15_deletePDF_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus("in progress")
        self.assertRaises(pdf.PDFGenerationInProgressError, pdfGen.deletePDF)
        
if __name__ == '__main__':
    unittest.main()
