import sys
import os
import unittest
import shutil
import time
import mimetypes
import simplejson as json
import imghdr

import testutils
sys.path.append(os.path.abspath('..'))
import tiff
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")
IMG_DIR = os.path.join(DATA_DIR, "images")

class TestTIFFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        
    def test_01_convertImage_image(self):
        img = os.path.join(IMG_DIR, "Image_0015.JPEG")
        convertedIMG = os.path.join(TEST_DIR, "Image_0015.tiff")
        tiff.convertImage(img, TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
        
    def test_02_convertImage_invalidFile(self):
        pdf = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertRaises(tiff.TIFFImageError, tiff.convertImage, pdf, TEST_DIR)
        
    def test_03_convertImage_invalidImagePath(self):
        img = os.path.join(IMG_DIR, "InvalidPath.JPEG")
        self.assertRaises(tiff.TIFFImageError, tiff.convertImage, img, TEST_DIR)
        
    def test_04_convertImage_invalidOutputDir(self):
        img = os.path.join(IMG_DIR, "Image_0015.JPEG")
        self.assertRaises(tiff.TIFFConversionError, tiff.convertImage, img, os.path.join(TEST_DIR, "invalidDir"))
        
    def test_05_convertImage_convertedAlreadyExists(self):
        img = os.path.join(IMG_DIR, "Image_0015.JPEG")
        convertedIMG = os.path.join(TEST_DIR, "Image_0015.tiff")
        shutil.copy(img, convertedIMG)
        tiff.convertImage(img, TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
        
#    def test_06_convertPagesToTIFF_image(self):
#        tiffDir = os.path.join(TEST_DIR, "tiffDir")
#        tiffImg = os.path.join(tiffDir, "Image_0015.tiff")
#        pages = [os.path.join(IMAGES_DIR, "Image_0015.JPEG")]
#        os.makedirs(tiffDir)
#        pdf.convertPagesToTIFF(pages, tiffDir)
#        self.assertTrue(os.path.exists(tiffImg), "The tiff version of the file should have been created")
#        self.assertEquals("image/tiff", mimetypes.guess_type(tiffImg)[0])
#        
#    def test_07_convertPagesToTIFF_empty(self):
#        tiffDir = os.path.join(TEST_DIR, "tiffDir")
#        pages = []
#        os.makedirs(tiffDir)
#        pdf.convertPagesToTIFF(pages, tiffDir)
#        self.assertEquals(0, len(os.listdir(tiffDir)))
#        
#    def test_08_convertPagesToTIFF_other(self):
#        tiffDir = os.path.join(TEST_DIR, "tiffDir")
#        pages = [os.path.join(TEST_DIR, "pdf/Decapod.pdf")]
#        os.makedirs(tiffDir)
#        pdf.convertPagesToTIFF(pages, tiffDir)
#        self.assertEquals(0, len(os.listdir(tiffDir)))
        
if __name__ == '__main__':
    unittest.main()
