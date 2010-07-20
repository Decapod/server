import os
import glob
import sys
import shutil
sys.path.append(os.path.abspath('..'))
import resourcesource

capturedImagesTestDir = "data/book/capturedImages/"

def cleanUpDir(dir):
    filePaths = glob.glob(dir + "/*")
    for filePath in filePaths:
        os.remove(filePath)  
        
def cleanUpCapturedImages():
    cleanUpDir(capturedImagesTestDir)

def deleteTestCapturedImagesDir():
    shutil.rmtree(capturedImagesTestDir)
    
def createTestResourceSource():
    return resourcesource.ResourceSource("data/resource-source-test-data.json")
