import sys
import os
import shutil
import unittest

sys.path.append(os.path.abspath('..'))
import imageprocessing
import resourcesource

class ImageProcessingTest(unittest.TestCase):
    
    resources = None
    processor = None

    def setUp(self):
        self.resources = resourcesource.ResourceSource("data/resource-source-test-data.json")
        self.processor = imageprocessing.ImageProcessor(self.resources)
        # Copy the images directory to a temporary directory we can clean up.
        shutil.copytree(self.resources.filePath("${testData}/images"), \
                        self.resources.filePath("${testData}/images/tmp"))
        
    def tearDown(self):
        # Clean up generated images after test run.
        shutil.rmtree(self.resources.filePath("${testData}/images/tmp"))

    def test_thumbnail(self):
        thumbPath = self.processor.thumbnail("${testData}/images/tmp/cat.jpg")
        self.assertEquals(thumbPath, "${testData}/images/tmp/cat-thumb.jpg")
        self.assertTrue(os.path.exists(self.resources.filePath(thumbPath)))
    
    def test_stitch(self):
        stitchPath = self.processor.stitch("${testData}/images/tmp/cat.jpg",\
                                           "${testData}/images/tmp/cactus.jpg")
        self.assertEquals(stitchPath, "${testData}/images/tmp/cat-cactus.png")
        self.assertTrue(os.path.exists(self.resources.filePath(stitchPath)))
