import sys
import os
import unittest
import shutil
import imghdr
import zipfile

sys.path.append(os.path.abspath('..'))
import image
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")
IMG_DIR = os.path.join(DATA_DIR, "images")
TEMP_DIR = os.path.join(TEST_DIR, "temp")
ZIP_FILE = os.path.join(TEST_DIR, "test.zip")
JPEG1 = "Image_0015.JPEG"
JPEG2 = "Image_0016.JPEG"
TIFF1 = "Image_0015.tiff"
TIFF2 = "Image_0016.tiff"
PNG1 = "Image_0015.png"
PNG2 = "Image_0016.png"

class TestTIFFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        
    def test_01_convert(self):
        img = os.path.join(IMG_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        image.convert(img, "tiff", TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
    
    def test_02_convert_defaultDir(self):
        img = os.path.join(TEST_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, PNG1)
        shutil.copy(os.path.join(IMG_DIR, JPEG1), TEST_DIR)
        image.convert(img, "png")
        self.assertEquals("png", imghdr.what(convertedIMG))
        
    def test_03_convert_invalidFile(self):
        pdf = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertRaises(image.ImageError, image.convert, pdf, "tiff", TEST_DIR)
        
    def test_04_convert_invalidImagePath(self):
        img = os.path.join(IMG_DIR, "InvalidPath.JPEG")
        self.assertRaises(image.ImageError, image.convert, img, "tiff", TEST_DIR)
        
    def test_05_convert_invalidOutputDir(self):
        img = os.path.join(IMG_DIR, JPEG1)
        self.assertRaises(image.ConversionError, image.convert, img, "tiff", os.path.join(TEST_DIR, "invalidDir"))
        
    def test_06_convert_convertedAlreadyExists(self):
        img = os.path.join(IMG_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        shutil.copy(img, convertedIMG)
        image.convert(img, "tiff", TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
        
    def test_07_convert_invalidFormat(self):
        img = os.path.join(IMG_DIR, JPEG1)
        convertedIMG = image.convert(img, "invalid", TEST_DIR)
        self.assertEquals("jpeg", imghdr.what(convertedIMG))
    
    def test_08_batchConvert(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff", TEST_DIR)
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertListEqual(expectedPaths, convertedImages)
            
    def test_09_batchConvert_defaultDir(self):
        shutil.copy(os.path.join(IMG_DIR, JPEG1), TEST_DIR)
        shutil.copy(os.path.join(IMG_DIR, JPEG2), TEST_DIR)
        images = [os.path.join(TEST_DIR, JPEG1), os.path.join(TEST_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff")
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertListEqual(expectedPaths, convertedImages)
    
    def test_10_batchConvert_invalidFile(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2), os.path.join(DATA_DIR, "pdf", "Decapod.pdf")]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff", TEST_DIR)
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.pdf")))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.tiff")))
        self.assertListEqual(expectedPaths, convertedImages)
        
    def test_11_batchConvert_invalidOutputDir(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        self.assertRaises(image.ConversionError, image.batchConvert, images, "tiff", os.path.join(TEST_DIR, "invalidDir"))
        
    def test_11_archiveConvert(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        expectedFiles = [TIFF1, TIFF2]
        zip = image.archiveConvert(images, "tiff", ZIP_FILE, TEMP_DIR)
        self.assertEquals(ZIP_FILE, zip)
        self.assertTrue(zipfile.is_zipfile(zip))
        zf = zipfile.ZipFile(zip, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
            
    def test_12_archiveConvert_invalidFile(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2), os.path.join(DATA_DIR, "pdf", "Decapod.pdf")]
        expectedFiles = [TIFF1, TIFF2]
        zip = image.archiveConvert(images, "tiff", ZIP_FILE, TEMP_DIR)
        self.assertEquals(ZIP_FILE, zip)
        self.assertTrue(zipfile.is_zipfile(zip))
        zf = zipfile.ZipFile(zip, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
    
    def test_13_archiveConvert_invalidOutputPath(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        self.assertRaises(image.OutputPathError, image.archiveConvert, images, "tiff", TEST_DIR, TEMP_DIR)
  
if __name__ == '__main__':
    unittest.main()
