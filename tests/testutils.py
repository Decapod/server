import os
import glob
import sys
import shutil
import mimetypes
sys.path.append(os.path.abspath('..'))
import resourcesource

TEST_DIR_NAME = "tests"
CONFIG_PATH = "data/resource-source-test-data.json"
IMAGES_TEST_DIR = "data/book/images/"

def getCWDName():
    cwd = os.getcwd()
    return os.path.split(cwd)[1]

def getTestSafePath(path):
    '''
    Needed to fix paths between individual and package test runs.
    When running the whole suite of tests, the working directory is one level higher.
    '''
    dir = getCWDName()
    return path if dir == TEST_DIR_NAME else os.path.join(TEST_DIR_NAME, path)

def cleanUpDir(dir):
    filePaths = glob.glob(dir + "/*")
    for filePath in filePaths:
        os.remove(filePath)  
        
def cleanUpImages():
    cleanUpDir(getTestSafePath(IMAGES_TEST_DIR))

def deleteTestImagesDir():
    shutil.rmtree(getTestSafePath(IMAGES_TEST_DIR))
    
def createTestResourceSource():
    return resourcesource.ResourceSource(getTestSafePath(CONFIG_PATH))

class mockFileStream(object):
    def __init__(self, filePath):
        name, extension = os.path.splitext(filePath)
        self.file = open(filePath, 'rb')
        self.content_type = mockMimeType(filePath)

class mockMimeType(object):
    def __init__(self, filePath):
        self.value = mimetypes.guess_type(filePath)[0]
