import sys
import os
import unittest
import shutil
import imghdr
import zipfile

sys.path.append(os.path.abspath(os.path.join('..')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'utils')))
from mockClasses import mockResourceSource
import image
from utils import io

DATA_DIR = os.path.abspath("data/")
LIBRARY_DIR = os.path.join(DATA_DIR, "library/")
BOOK_DIR = os.path.join(LIBRARY_DIR, "book/")
IMG_DIR = os.path.join(BOOK_DIR, "images/")
TEST_DIR = os.path.join(DATA_DIR, "test_dir/")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
TEMP_DIR = os.path.join(TEST_DIR, "temp")
ZIP_FILE = os.path.join(TEST_DIR, "test.zip")

JPEG1 = "Image_0015.JPEG"
JPEG2 = "Image_0016.JPEG"
TIFF1 = "Image_0015.tiff"
TIFF2 = "Image_0016.tiff"
TIFF3 = "image.tiff"
PNG1 = "Image_0015.png"
PNG2 = "Image_0016.png"

class TestImageModuleFunctions(unittest.TestCase):
    
    def setUp(self):
        io.makeDirs(TEST_DIR)
            
    def tearDown(self):
        io.rmTree(TEST_DIR)
        
    def test_01_convert(self):
        img = os.path.join(IMAGES_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        image.convert(img, "tiff", TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
    
    def test_02_convert_defaultDir(self):
        img = os.path.join(TEST_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, PNG1)
        shutil.copy(os.path.join(IMAGES_DIR, JPEG1), TEST_DIR)
        image.convert(img, "png")
        self.assertEquals("png", imghdr.what(convertedIMG))
        
    def test_03_convert_invalidFile(self):
        pdf = os.path.join(DATA_DIR, "pdf", "Decapod.pdf")
        self.assertRaises(image.ImageError, image.convert, pdf, "tiff", TEST_DIR)
        
    def test_04_convert_invalidImagePath(self):
        img = os.path.join(IMAGES_DIR, "InvalidPath.JPEG")
        self.assertRaises(image.ImageError, image.convert, img, "tiff", TEST_DIR)
        
    def test_05_convert_invalidOutputDir(self):
        img = os.path.join(IMAGES_DIR, JPEG1)
        self.assertRaises(image.ConversionError, image.convert, img, "tiff", os.path.join(TEST_DIR, "invalidDir"))
        
    def test_06_convert_convertedAlreadyExists(self):
        img = os.path.join(IMAGES_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF1)
        shutil.copy(img, convertedIMG)
        image.convert(img, "tiff", TEST_DIR)
        self.assertEquals("tiff", imghdr.what(convertedIMG))
        
    def test_07_convert_invalidFormat(self):
        img = os.path.join(IMAGES_DIR, JPEG1)
        convertedIMG = image.convert(img, "invalid", TEST_DIR)
        self.assertEquals("jpeg", imghdr.what(convertedIMG))
    
    def test_08_convert_name(self):
        img = os.path.join(IMAGES_DIR, JPEG1)
        convertedIMG = os.path.join(TEST_DIR, TIFF3)
        image.convert(img, "tiff", TEST_DIR, os.path.splitext(TIFF3)[0])
        self.assertEquals("tiff", imghdr.what(convertedIMG))
    
    def test_09_batchConvert(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff", TEST_DIR)
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertListEqual(expectedPaths, convertedImages)
            
    def test_10_batchConvert_defaultDir(self):
        shutil.copy(os.path.join(IMAGES_DIR, JPEG1), TEST_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, JPEG2), TEST_DIR)
        images = [os.path.join(TEST_DIR, JPEG1), os.path.join(TEST_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff")
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertListEqual(expectedPaths, convertedImages)
        
    def test_11_batchConvert_nameTemplate(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        expectedPaths = [os.path.join(TEST_DIR, "image-1.tiff"), os.path.join(TEST_DIR, "image-2.tiff")]
        convertedImages = image.batchConvert(images, "tiff", TEST_DIR, "image-$index")
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertListEqual(expectedPaths, convertedImages)
    
    def test_12_batchConvert_invalidFile(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2), os.path.join(DATA_DIR, "pdf", "Decapod.pdf")]
        expectedPaths = [os.path.join(TEST_DIR, TIFF1), os.path.join(TEST_DIR, TIFF2)]
        convertedImages = image.batchConvert(images, "tiff", TEST_DIR)
        for img in convertedImages:
            self.assertEquals("tiff", imghdr.what(img))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.pdf")))
        self.assertFalse(os.path.exists(os.path.join(TEST_DIR, "Decapod.tiff")))
        self.assertListEqual(expectedPaths, convertedImages)
        
    def test_13_batchConvert_invalidOutputDir(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        self.assertRaises(image.ConversionError, image.batchConvert, images, "tiff", os.path.join(TEST_DIR, "invalidDir"))
        
    def test_14_archiveConvert(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        expectedFiles = [TIFF1, TIFF2]
        zip = image.archiveConvert(images, "tiff", ZIP_FILE, TEMP_DIR)
        self.assertEquals(ZIP_FILE, zip)
        self.assertTrue(zipfile.is_zipfile(zip))
        zf = zipfile.ZipFile(zip, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
        self.assertFalse(os.path.exists(TEMP_DIR))
        
    def test_15_archiveConvert_nameTemplate(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        expectedFiles = ["image-1.tiff", "image-2.tiff"]
        zip = image.archiveConvert(images, "tiff", ZIP_FILE, TEMP_DIR, "image-$index")
        self.assertEquals(ZIP_FILE, zip)
        self.assertTrue(zipfile.is_zipfile(zip))
        zf = zipfile.ZipFile(zip, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
        self.assertFalse(os.path.exists(TEMP_DIR))
            
    def test_16_archiveConvert_invalidFile(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2), os.path.join(DATA_DIR, "pdf", "Decapod.pdf")]
        expectedFiles = [TIFF1, TIFF2]
        zip = image.archiveConvert(images, "tiff", ZIP_FILE, TEMP_DIR)
        self.assertEquals(ZIP_FILE, zip)
        self.assertTrue(zipfile.is_zipfile(zip))
        zf = zipfile.ZipFile(zip, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
        self.assertFalse(os.path.exists(TEMP_DIR))
    
    def test_17_archiveConvert_invalidOutputPath(self):
        images = [os.path.join(IMAGES_DIR, JPEG1), os.path.join(IMAGES_DIR, JPEG2)]
        self.assertRaises(image.OutputPathError, image.archiveConvert, images, "tiff", TEST_DIR, TEMP_DIR)
        self.assertFalse(os.path.exists(TEMP_DIR))

#TODO: test that the status is set to "error" when archiveConvert throws an exception   
class TestImageExporter(unittest.TestCase):
    mockRS = mockResourceSource({"/library": {"path": LIBRARY_DIR, "url": "/library"}})
    
    def setUp(self):
        io.makeDirs(BOOK_DIR)
            
    def tearDown(self):
        io.rmTree(BOOK_DIR)
    
    def assertStatusFile(self, status, statusFile):
        readStatus = io.loadJSONFile(statusFile)
        self.assertDictEqual(status, readStatus)
    
    def test_01_init(self):
        expectedStatus = {"status": image.EXPORT_READY}
        imgExp = image.ImageExporter(self.mockRS)
        self.assertTrue(os.path.exists(os.path.join(BOOK_DIR, "export", "image")))
        self.assertDictEqual(expectedStatus, imgExp.status.model)
    
    def test_02_setStatus(self):
        st = "test"
        status = {"status": st}
        imgExp = image.ImageExporter(self.mockRS)
        imgExp.setStatus(st)
        self.assertStatusFile(status, imgExp.statusFilePath)
        self.assertDictEqual(status, imgExp.status.model)
       
    def test_03_setStatus_removeURL(self):
        st = "test"
        newStatus = {"status": st}
        imgExp = image.ImageExporter(self.mockRS)
        imgExp.status.update("status", "complete")
        imgExp.status.update("url", "localhost")        
        imgExp.setStatus(st)
        self.assertStatusFile(newStatus, imgExp.statusFilePath)
        self.assertDictEqual(newStatus, imgExp.status.model)
      
    def test_04_setStatus_addURL(self):
        st = "complete"
        completeStatus = {"status": st, "url": "/library/book/export/image/Decapod.zip"}
        imgExp = image.ImageExporter(self.mockRS)
        imgExp.setStatus(st, includeURL=True)
        self.assertStatusFile(completeStatus, imgExp.statusFilePath)
        self.assertDictEqual(completeStatus, imgExp.status.model)
    
    def test_05_getStatus(self):
        expectedStatusStr = {"status": "ready"}
        imgExp = image.ImageExporter(self.mockRS)
        self.assertDictEqual(expectedStatusStr, imgExp.getStatus())
    
    def test_06_export(self):
        completeStatus = {"status": image.EXPORT_COMPLETE, "url": "/library/book/export/image/Decapod.zip"}
        expectedFiles = ["Image_0015.tiff"]
        imgExp = image.ImageExporter(self.mockRS)
        io.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = imgExp.export("tiff")
        self.assertTrue(os.path.exists(imgExp.archivePath), "The output file should exist at path {0}".format(imgExp.archivePath))
        self.assertDictEqual(completeStatus, imgExp.status.model)
        self.assertDictEqual(completeStatus, returnedStatus)
        self.assertDictEqual(completeStatus, io.loadJSONFile(imgExp.statusFilePath))
        zf = zipfile.ZipFile(imgExp.archivePath, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
    
    def test_07_export_nameTemplate(self):
        completeStatus = {"status": image.EXPORT_COMPLETE, "url": "/library/book/export/image/Decapod.zip"}
        expectedFiles = ["image-1.tiff"]
        imgExp = image.ImageExporter(self.mockRS, nameTemplate="image-$index")
        io.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        returnedStatus = imgExp.export("tiff")
        self.assertTrue(os.path.exists(imgExp.archivePath), "The output file should exist at path {0}".format(imgExp.archivePath))
        self.assertDictEqual(completeStatus, imgExp.status.model)
        self.assertDictEqual(completeStatus, returnedStatus)
        self.assertDictEqual(completeStatus, io.loadJSONFile(imgExp.statusFilePath))
        zf = zipfile.ZipFile(imgExp.archivePath, 'r')
        self.assertIsNone(zf.testzip()) # testzip returns None if no errors are found in the zip file
        self.assertListEqual(expectedFiles, zf.namelist())
        zf.close()
    
    def test_08_export_exception_errorDuringArchive(self):
        errorStatus = {"status": image.EXPORT_ERROR}
        imgExp = image.ImageExporter(self.mockRS)
        io.makeDirs(IMG_DIR)
        shutil.copy(os.path.join(IMAGES_DIR, "Image_0015.JPEG"), IMG_DIR)
        imgExp.archivePath = os.path.join(BOOK_DIR, "invalidPath", "invalid.zip") #sets the archivePath to an invalid path to force the exception
        self.assertRaises(image.OutputPathError, imgExp.export, "tiff")
        self.assertFalse(os.path.exists(imgExp.archivePath), "The output file should not exist at path {0}".format(imgExp.archivePath))
        self.assertDictEqual(errorStatus, imgExp.status.model)
        self.assertDictEqual(errorStatus, io.loadJSONFile(imgExp.statusFilePath))
    
    def test_09_export_exception_noImages(self):
        imgExp = image.ImageExporter(self.mockRS)
        io.makeDirs(IMG_DIR)
        self.assertRaises(image.ImagesNotFoundError, imgExp.export, "tiff")
    
    def test_10_export_exception_inProgress(self):
        imgExp = image.ImageExporter(self.mockRS)
        imgExp.status.update("status", image.EXPORT_IN_PROGRESS)
        self.assertRaises(image.ExportInProgressError, imgExp.export, "tiff")
    
    def test_11_delete(self):
        imgExp = image.ImageExporter(self.mockRS)
        shutil.copy(os.path.join(DATA_DIR, "pdf", "Decapod.pdf"), imgExp.archivePath)
        self.assertTrue(os.path.exists(imgExp.archivePath), "The zip file should be copied over")
        imgExp.deleteExport()
        self.assertTrue(os.path.exists(imgExp.imgDirPath), "The path {0} should exist".format(imgExp.imgDirPath))
        self.assertFalse(os.path.exists(imgExp.archivePath), "The zip file at path {0} should not exist".format(imgExp.archivePath))
    
    def test_12_delete_exception(self):
        imgExp = image.ImageExporter(self.mockRS)
        imgExp.status.update("status", image.EXPORT_IN_PROGRESS)
        self.assertRaises(image.ExportInProgressError, imgExp.deleteExport)
  
if __name__ == '__main__':
    unittest.main()
