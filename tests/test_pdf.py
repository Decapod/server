import sys
import os
import unittest
import shutil
import time
import mimetypes

import testutils
sys.path.append(os.path.abspath('..'))
import pdf

DATA_DIR = os.path.abspath("data/")
BOOK_DIR = os.path.join(DATA_DIR, "library/book/")
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

    # TODO: test order of pages in array. Should be sorted by last modified.
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
