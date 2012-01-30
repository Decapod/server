import sys
import os
import unittest
import shutil
import time
import mimetypes
import simplejson as json

import testutils
sys.path.append(os.path.abspath('..'))
import pdf
import decapod_utilities as utils

MOCK_IMG_DIR = os.path.normpath(os.path.abspath("../mock-images/"))
DATA_DIR = os.path.abspath("data/")
LIBRARY_PATH = os.path.join(DATA_DIR, "library/")
BOOK_DIR = os.path.join(LIBRARY_PATH, "book/")
IMG_DIR = os.path.join(BOOK_DIR, "images/")
PDF_DIR = os.path.join(IMG_DIR, "pdf/")
STATUS_FILE = os.path.join(PDF_DIR, "exportStatus.json")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

class TestPDFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        utils.rmTree(BOOK_DIR)
        
    def test_01_isImage_image(self):
        image = os.path.join(DATA_DIR, "images/cactus.jpg")
        self.assertTrue(pdf.isImage(image), "The file at path ({0}) should be an image".format(image))
        
    def test_02_isImage_other(self):
        file = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        self.assertFalse(pdf.isImage(file), "The file at path ({0}) should not be an image".format(file))
        
    def test_03_lastModified_newFile(self):
        newDir = os.path.join(TEST_DIR, "new_dir")
        os.makedirs(newDir)
        curretnAppoxTime = int(time.time())
        modified = pdf.lastModified(newDir)
        self.assertAlmostEquals(curretnAppoxTime, modified)
    
    def test_04_lastModified_modified(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        firstContent = "New File"
        secondContent = "Modified File"
        utils.writeToFile(firstContent, filePath)
        firstModTime = pdf.lastModified(filePath)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        utils.writeToFile(secondContent, filePath)
        secondModTime = pdf.lastModified(filePath)
        self.assertNotEquals(firstModTime, secondModTime)
        self.assertTrue(firstModTime < secondModTime, "The first modification time stamp should be smaller than the second")

    def test_05_bookPagesToArray_images(self):
        imgOne = os.path.join(DATA_DIR, "images/cactus.jpg")
        imgTwo = os.path.join(DATA_DIR, "images/cat.jpg")
        shutil.copy(imgOne, TEST_DIR)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        shutil.copy(imgTwo, TEST_DIR)
        pages = pdf.bookPagesToArray(TEST_DIR)
        self.assertEquals(2, len(pages))
        self.assertTrue(pdf.lastModified(pages[0]) < pdf.lastModified(pages[1]), "The first page in the array should have been modified prior to the second")
        
    def test_06_bookPagesToArray_other(self):
        pdfDir = os.path.join(DATA_DIR, "pdf")
        pages = pdf.bookPagesToArray(pdfDir)
        self.assertEquals(0, len(pages))
        
    def test_07_bookPagesToArray_mixed(self):
        imgOne = os.path.join(DATA_DIR, "images/cactus.jpg")
        imgTwo = os.path.join(DATA_DIR, "images/cat.jpg")
        pdfOne = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        shutil.copy(imgOne, TEST_DIR)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        shutil.copy(imgTwo, TEST_DIR)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        shutil.copy(pdfOne, TEST_DIR)
        pages = pdf.bookPagesToArray(TEST_DIR)
        self.assertEquals(2, len(pages))
        self.assertTrue(pdf.lastModified(pages[0]) < pdf.lastModified(pages[1]), "The first page in the array should have been modified prior to the second")
        
    def test_08_convertPagesToTIFF_image(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        tiffImg = os.path.join(tiffDir, "cactus.tiff")
        pages = [os.path.join(DATA_DIR, "images/cactus.jpg")]
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertTrue(os.path.exists(tiffImg), "The tiff version of the file should have been created")
        self.assertEquals("image/tiff", mimetypes.guess_type(tiffImg)[0])
        
    def test_09_convertPagesToTIFF_empty(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        pages = []
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertEquals(0, len(os.listdir(tiffDir)))
        
    def test_10_convertPagesToTIFF_other(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        pages = [os.path.join(TEST_DIR, "pdf/Decapod.pdf")]
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertEquals(0, len(os.listdir(tiffDir)))

class TestPDFGenerator(unittest.TestCase):
    book = None
    mockRS = testutils.mockResourceSource({"/library": {"path": LIBRARY_PATH, "url": "/library"}})
    
    def setUp(self):
        utils.makeDirs(IMG_DIR)
        
    def tearDown(self):
        utils.rmTree(BOOK_DIR)
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        file = open(statusFile)
        read = file.read()
        file.close()
        self.assertEquals(status, read)
    
    def assertInit(self, PDFGenerator, status):
        self.assertEquals(IMG_DIR, PDFGenerator.bookDirPath)
        self.assertEquals(PDF_DIR, PDFGenerator.pdfDirPath)
        self.assertEquals(os.path.join(PDF_DIR, "genPDFTemp"), PDFGenerator.tempDirPath)
        self.assertEquals(os.path.join(PDF_DIR, "tiffTemp"), PDFGenerator.tiffDirPath)
        self.assertEquals(STATUS_FILE, PDFGenerator.statusFilePath)
        self.assertEquals(os.path.join(PDF_DIR, "Decapod.pdf"), PDFGenerator.pdfPath)
        self.assertEquals(None, PDFGenerator.pages)
        self.assertEquals(None, PDFGenerator.tiffPages)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(PDFGenerator.status))
        self.assertTrue(os.path.exists(PDF_DIR), "The pdf directory ({0}) should exist".format(PDF_DIR))
            
    def test_01_init(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertInit(pdfGen, '{"status": "none"}')
            
    def test_02_init_statusFile(self):
        status = '{"status": "in progress"}'
        utils.makeDirs(PDF_DIR)
        # write status file
        file = open(STATUS_FILE, "w")
        file.write(status)
        file.close()
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertInit(pdfGen, status)
        
    def test_03_writeToStatusFile(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        status = '{"status": "test"}'
        pdfGen.status = json.loads(status)
        pdfGen.writeToStatusFile()
        self.assertStatusFile(status)
    
    def test_04_setStatus(self):
        st = "test"
        status = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(st)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        
    def test_05_setStatus_removeURL(self):
        st = "test"
        oldStatus = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        newStatus = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.status = json.loads(oldStatus)
        pdfGen.setStatus(st)
        self.assertStatusFile(newStatus)
        self.assertEquals(newStatus, json.dumps(pdfGen.status))
        
    def test_06_setStatus_complete(self):
        st = "complete"
        status = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus(st)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        
    def test_07_getStatus(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        status = pdfGen.getStatus()
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
    
    def test_08_generatePDFFromPages(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        tiffTempDir = os.path.join(PDF_DIR, "tiffTemp")
        utils.makeDirs(tiffTempDir)
        shutil.copy(os.path.join(MOCK_IMG_DIR, "Image_0015.JPEG"), IMG_DIR)
        pdfGen.tiffPages = pdf.convertPagesToTIFF([os.path.join(IMG_DIR, "Image_0015.JPEG")], tiffTempDir)
        pdf.PDFGenerationError, pdfGen.generatePDFFromPages()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
    
    def test_09_generatePDFFromPages_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.tiffPages = []
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generatePDFFromPages)
        
    def test_10_generate(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        status = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        utils.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(MOCK_IMG_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = pdfGen.generate()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        self.assertEquals(status, returnedStatus)
        
    def test_11_generate_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generate)
        
    def test_12_deletePDF(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        utils.makeDirs(PDF_DIR)
        shutil.copy(os.path.join(DATA_DIR, "pdf/Decapod.pdf"), PDF_DIR)
        pdfGen.setStatus("complete")
        pdfGen.deletePDF()
        self.assertInit(pdfGen, '{"status": "none"}')
        self.assertFalse(os.path.exists(os.path.join(PDF_DIR, "Decapod.pdf")), "The export pdf should not exist")
        
    def test_13_deletePDF_exception(self):
        pdfGen = pdf.PDFGenerator(self.mockRS)
        pdfGen.setStatus("in progress")
        self.assertRaises(pdf.PDFGenerationError, pdfGen.deletePDF)
        
if __name__ == '__main__':
    unittest.main()
