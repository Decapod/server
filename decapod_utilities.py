import os
import imghdr
import shutil
import subprocess

def makeDirs(path, mode=0777):
    if not os.path.exists(path):
        os.makedirs(path, mode)

def rmTree(path, ignore_errors=False, onerror=None):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors, onerror)
        
def writeToFile(contents, writePath, writeMode="w"):
    f = open(writePath, writeMode)
    f.write(contents)
    f.close()
    
def invokeCommandSync(cmdArgs, error, message):
    proc = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
    output = proc.communicate()[0]
    if proc.returncode != 0:
        print(output)
        raise error, message
    
    return output

def isImage(filePath):
    return os.path.isfile(filePath) and imghdr.what(filePath) != None

def imageDirToList(imageDir, sortKey=None, reverse=False):
    '''
    Takes a directory and returns a list of image paths.
    Can optionally provide sort options (sortKey for the method to sort by, and reverse to specify the direction)
    By default the list is sorted alphabetically.
    '''
    allImages = []
    for fileName in os.listdir(imageDir):
        filePath = os.path.join(imageDir, fileName)
        
        if isImage(filePath): 
            allImages.append(filePath)
    return sorted(allImages, key=sortKey, reverse=reverse)
