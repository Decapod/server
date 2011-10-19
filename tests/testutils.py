import os
import glob
import sys
import shutil
import mimetypes
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

class mockFileStream(object):
    file = None
    type = None
    def __init__(self, filePath):
        name, extension = os.path.splitext(filePath)
        self.file = open(filePath, 'rb')
        self.type = mimetypes.guess_type(filePath)[0]
