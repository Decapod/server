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

MOCK_IMG_DIR = os.path.normpath(os.path.abspath("../mock-images/"))
DATA_DIR = os.path.abspath("data/")
BOOK_DIR = os.path.join(DATA_DIR, "library/book/")
IMG_DIR = os.path.join(BOOK_DIR, "images/")
PDF_DIR = os.path.join(IMG_DIR, "pdf/")
STATUS_FILE = os.path.join(PDF_DIR, "exportStatus.json")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")

class TestPDFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        if not os.path.exists(TEST_DIR):
            os.makedirs(TEST_DIR)
            
    def tearDown(self):
        if os.path.exists(TEST_DIR):
            shutil.rmtree(TEST_DIR)
        if os.path.exists(BOOK_DIR):
            shutil.rmtree(BOOK_DIR)
    
    def test_01_createDir(self):
        newDir = os.path.join(TEST_DIR, "new_dir")
        self.assertFalse(os.path.exists(newDir), "The directory at path ({0}) should not yet exist".format(newDir))
        #tested function
        pdf.createDir(newDir)
        self.assertTrue(os.path.exists(newDir), "The directory at path ({0}) should have been created".format(newDir))
        
    def test_02_writeToFile(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        content = "Test File"
        self.assertFalse(os.path.exists(filePath), "The file at path ({0}) should not yet exist".format(filePath))
        #tested function
        pdf.writeToFile(content, filePath)
        self.assertTrue(os.path.exists(filePath), "The file at path ({0}) should have been created".format(filePath))
        # read in file
        file = open(filePath, "r")
        read = file.read()
        file.close()
        self.assertEquals(content, read)
        
    def test_03_isImage_image(self):
        image = os.path.join(DATA_DIR, "images/cactus.jpg")
        self.assertTrue(pdf.isImage(image), "The file at path ({0}) should be an image".format(image))
        
    def test_03_isImage_other(self):
        file = os.path.join(DATA_DIR, "pdf/Decapod.pdf")
        self.assertFalse(pdf.isImage(file), "The file at path ({0}) should not be an image".format(file))
        
    def test_04_lastModified_newFile(self):
        newDir = os.path.join(TEST_DIR, "new_dir")
        os.makedirs(newDir)
        curretnAppoxTime = int(time.time())
        modified = pdf.lastModified(newDir)
        self.assertAlmostEquals(curretnAppoxTime, modified)
    
    def test_05_lastModified_modified(self):
        filePath = os.path.join(TEST_DIR, "testFile.txt")
        firstContent = "New File"
        secondContent = "Modified File"
        file = open(filePath, "w")
        file.write(firstContent)
        firstModTime = pdf.lastModified(filePath)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        file.write(secondContent)
        file.close()
        secondModTime = pdf.lastModified(filePath)
        self.assertNotEquals(firstModTime, secondModTime)
        self.assertTrue(firstModTime < secondModTime, "The first modification time stamp should be smaller than the second")

    def test_06_bookPagesToArray_images(self):
        imgOne = os.path.join(DATA_DIR, "images/cactus.jpg")
        imgTwo = os.path.join(DATA_DIR, "images/cat.jpg")
        shutil.copy(imgOne, TEST_DIR)
        time.sleep(1) # wait 1 second. Needed because the lastModified time isn't precise enough 
        shutil.copy(imgTwo, TEST_DIR)
        pages = pdf.bookPagesToArray(TEST_DIR)
        self.assertEquals(2, len(pages))
        self.assertTrue(pdf.lastModified(pages[0]) < pdf.lastModified(pages[1]), "The first page in the array should have been modified prior to the second")
        
    def test_07_bookPagesToArray_other(self):
        pdfDir = os.path.join(DATA_DIR, "pdf")
        pages = pdf.bookPagesToArray(pdfDir)
        self.assertEquals(0, len(pages))
        
    def test_08_bookPagesToArray_mixed(self):
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
        
    def test_09_convertPagesToTIFF_image(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        tiffImg = os.path.join(tiffDir, "cactus.tiff")
        pages = [os.path.join(DATA_DIR, "images/cactus.jpg")]
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertTrue(os.path.exists(tiffImg), "The tiff version of the file should have been created")
        self.assertEquals("image/tiff", mimetypes.guess_type(tiffImg)[0])
        
    def test_10_convertPagesToTIFF_empty(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        pages = []
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertEquals(0, len(os.listdir(tiffDir)))
        
    def test_11_convertPagesToTIFF_other(self):
        tiffDir = os.path.join(TEST_DIR, "tiffDir")
        pages = [os.path.join(TEST_DIR, "pdf/Decapod.pdf")]
        os.makedirs(tiffDir)
        pdf.convertPagesToTIFF(pages, tiffDir)
        self.assertEquals(0, len(os.listdir(tiffDir)))

class TestPDFGenerator(unittest.TestCase):
    
    resources = None
    book = None
    
    def setUp(self):
        self.resources = testutils.createTestResourceSource()
        if not os.path.exists(IMG_DIR):
            os.makedirs(IMG_DIR)
        
    def tearDown(self):
        if os.path.exists(BOOK_DIR):
            shutil.rmtree(BOOK_DIR)
    
    def assertStatusFile(self, status, statusFile = STATUS_FILE):
        file = open(statusFile)
        read = file.read()
        file.close()
        self.assertEquals(status, read)
    
    def assertInit(self, PDFGenerator, status):
        self.assertEquals(self.resources, PDFGenerator.resources)
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
        pdfGen = pdf.PDFGenerator(self.resources)
        self.assertInit(pdfGen, '{"status": "none"}')
            
    def test_02_init_statusFile(self):
        status = '{"status": "in progress"}'
        if not os.path.exists(PDF_DIR):
            os.makedirs(PDF_DIR)
        # write status file
        file = open(STATUS_FILE, "w")
        file.write(status)
        file.close()
        pdfGen = pdf.PDFGenerator(self.resources)
        self.assertInit(pdfGen, status)
        
    def test_03_clearExportDir(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.clearExportDir()
        self.assertFalse(os.path.exists(PDF_DIR), "The pdf directory, at path ({0}), should have been removed".format(PDF_DIR))
        
    def test_04_writeToStatusFile(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        status = '{"status": "test"}'
        pdfGen.status = json.loads(status)
        pdfGen.writeToStatusFile()
        self.assertStatusFile(status)
    
    def test_05_setStatus(self):
        st = "test"
        status = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.setStatus(st)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        
    def test_06_setStatus_removeURL(self):
        st = "test"
        oldStatus = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        newStatus = '{"status": "test"}'
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.status = json.loads(oldStatus)
        pdfGen.setStatus(st)
        self.assertStatusFile(newStatus)
        self.assertEquals(newStatus, json.dumps(pdfGen.status))
        
    def test_07_setStatus_complete(self):
        st = "complete"
        status = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.setStatus(st)
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        
    def test_08_getStatus(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        status = pdfGen.getStatus()
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
    
    def test_09_generatePDFFromPages(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        tiffTempDir = os.path.join(PDF_DIR, "tiffTemp")
        if not os.path.exists(tiffTempDir):
            os.makedirs(tiffTempDir)
        shutil.copy(os.path.join(MOCK_IMG_DIR, "Image_0015.JPEG"), IMG_DIR)
        pdfGen.tiffPages = pdf.convertPagesToTIFF([os.path.join(IMG_DIR, "Image_0015.JPEG")], tiffTempDir)
        pdf.PDFGenerationError, pdfGen.generatePDFFromPages()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
    
    def test_10_generatePDFFromPages_exception(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.tiffPages = []
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generatePDFFromPages)
        
    def test_11_generate(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        status = '{"status": "complete", "downloadSRC": "/library/book/images/pdf/Decapod.pdf"}'
        if not os.path.exists(IMG_DIR):
            os.makedirs(IMG_DIR)
        shutil.copy(os.path.join(MOCK_IMG_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = pdfGen.generate()
        self.assertTrue(os.path.exists(pdfGen.pdfPath), "The output file should exist at path {0}".format(pdfGen.pdfPath))
        self.assertStatusFile(status)
        self.assertEquals(status, json.dumps(pdfGen.status))
        self.assertEquals(status, returnedStatus)
        
    def test_12_generate_exception(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        self.assertRaises(pdf.PDFGenerationError, pdfGen.generate)
        
    def test_13_deletePDF(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        if not os.path.exists(PDF_DIR):
            os.makedirs(PDF_DIR)
        shutil.copy(os.path.join(DATA_DIR, "pdf/Decapod.pdf"), PDF_DIR)
        pdfGen.setStatus("complete")
        pdfGen.deletePDF()
        self.assertInit(pdfGen, '{"status": "none"}')
        self.assertFalse(os.path.exists(os.path.join(PDF_DIR, "Decapod.pdf")), "The export pdf should not exist")
        
    def test_14_deletePDF_exception(self):
        pdfGen = pdf.PDFGenerator(self.resources)
        pdfGen.setStatus("in progress")
        self.assertRaises(pdf.PDFGenerationError, pdfGen.deletePDF)