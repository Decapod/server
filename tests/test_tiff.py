import sys
import os
import unittest
import shutil
import imghdr

sys.path.append(os.path.abspath('..'))
import tiff
import decapod_utilities as utils

DATA_DIR = os.path.abspath("data/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")
IMG_DIR = os.path.join(DATA_DIR, "images")
JPEG1 = "Image_0015.JPEG"
JPEG2 = "Image_0016.JPEG"
TIFF1 = "Image_0015.tiff"
TIFF2 = "Image_0016.tiff"

class TestTIFFModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        utils.makeDirs(TEST_DIR)
            
    def tearDown(self):
        utils.rmTree(TEST_DIR)
        
    def test_01_convertImage(self):
        img = os.path.join(IMG_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        tiff.convertImage(img, TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
    
    def test_02_convertImage_defaultDir(self):
        img = os.path.join(TEST_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        shutil.copy(os.path.join(IMG_DIR, JPEG1), TEST_DIR)
        tiff.convertImage(img)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
        
    def test_03_convertImage_invalidFile(self):
        pdf = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertRaises(tiff.TIFFImageError, tiff.convertImage, pdf, TEST_DIR)
        
    def test_04_convertImage_invalidImagePath(self):
        img = os.path.join(IMG_DIR, "InvalidPath.JPEG")
        self.assertRaises(tiff.TIFFImageError, tiff.convertImage, img, TEST_DIR)
        
    def test_05_convertImage_invalidOutputDir(self):
        img = os.path.join(IMG_DIR, JPEG1)
        self.assertRaises(tiff.TIFFConversionError, tiff.convertImage, img, os.path.join(TEST_DIR, "invalidDir"))
        
    def test_06_convertImage_convertedAlreadyExists(self):
        img = os.path.join(IMG_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        shutil.copy(img, convertedIMG)
        tiff.convertImage(img, TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
    
    def test_07_convertImages(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = tiff.convertImages(images, TEST_DIR)
        for image in convertedImages:
            self.assertEquals("tiff", imghdr.what(image))
        self.assertListEqual(expectedPaths, convertedImages)
            
    def test_08_convertedImages_defaultDir(self):
        shutil.copy(os.path.join(IMG_DIR, JPEG1), TEST_DIR)
        shutil.copy(os.path.join(IMG_DIR, JPEG2), TEST_DIR)
        images = [os.path.join(TEST_DIR, JPEG1), os.path.join(TEST_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = tiff.convertImages(images)
        for image in convertedImages:
            self.assertEquals("tiff", imghdr.what(image))
        self.assertListEqual(expectedPaths, convertedImages)
    
    def test_09_convertedImages_invalidFile(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2), os.path.join(DATA_DIR, "pdf", "Decapod.pdf")]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = tiff.convertImages(images, TEST_DIR)
        for image in convertedImages:
            self.assertEquals("tiff", imghdr.what(image))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.pdf")))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.tiff")))
        self.assertListEqual(expectedPaths, convertedImages)
        
    def test_10_convertImages_invalidOutputDir(self):
        images = [os.path.join(IMG_DIR, JPEG1), os.path.join(IMG_DIR, JPEG2)]
        self.assertRaises(tiff.TIFFConversionError, tiff.convertImages, images, os.path.join(TEST_DIR, "invalidDir"))
        
if __name__ == '__main__':
    unittest.main()
