import sys
import os
import shutil
import unittest
from PIL import Image

sys.path.append(os.path.abspath('..'))
import imageprocessing
import resourcesource

class ImageProcessingTest(unittest.TestCase):
    
    resources = None
    processor = None
    testDataDir = None
    
    def setUp(self):
        self.resources = resourcesource.ResourceSource("data/resource-source-test-data.json")
        self.testDataDir = self.resources.filePath("${testData}")
        
        # Copy the images directory to a temporary directory we can clean up.
        shutil.copytree(self.resources.filePath("${testData}/images"), \
                        self.resources.filePath("${testData}/images/tmp"))
        
    def tearDown(self):
        # Clean up generated images after test run.
        shutil.rmtree(self.resources.filePath("${testData}/images/tmp"))

    def test_thumbnail(self):
        thumbPath = imageprocessing.thumbnail(self.testDataDir + "/images/tmp/cat.jpg")
        self.assertEquals(thumbPath, self.testDataDir + "/images/tmp/cat-thumb.jpg")
        self.assertTrue(os.path.exists(thumbPath))
    
    def test_stitch(self):
        stitchPath = imageprocessing.stitch(self.testDataDir + "/images/tmp/cat.jpg",\
                                            self.testDataDir + "/images/tmp/cactus.jpg")
        self.assertEquals(stitchPath, self.testDataDir + "/images/tmp/cat-cactus.png")
        self.assertTrue(os.path.exists(stitchPath))

        # Ensure that the stitched image is correctly oriented relative to the input images
        expectedHeight = 600 # px
        stitched = Image.open(stitchPath)
        self.assertEquals(expectedHeight, stitched.size[1])
        
    def test_rotate(self):
        # Sanity check the image before rotating it
        sourceImage = self.testDataDir + "/images/tmp/cactus.jpg"
        expectedSize = (480, 320)
        unrotated = Image.open(sourceImage)
        self.assertEquals(expectedSize, unrotated.size)
        
        # Rotate 90 degrees
        rotatedPath = imageprocessing.rotate(sourceImage, 90)
        self.assertEquals(rotatedPath, self.testDataDir + "/images/tmp/cactus.jpg")
        self.assertTrue(os.path.exists(rotatedPath))
        expectedSize = (320, 480)
        rotated = Image.open(rotatedPath)
        self.assertEquals(expectedSize, rotated.size)
        