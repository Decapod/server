import os
import glob
import sys
import shutil
sys.path.append(os.path.abspath('..'))
import resourcesource

capturedImagesTestDir = "data/book/capturedImages/"

def cleanUpCapturedImages():
    imagePaths = glob.glob(capturedImagesTestDir + "*")
    for imagePath in imagePaths:
        os.remove(imagePath)

def deleteTestCapturedImagesDir():
    shutil.rmtree(capturedImagesTestDir)
    
def createTestResourceSource():
    return resourcesource.ResourceSource("data/resource-source-test-data.json")
