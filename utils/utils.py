import os
import imghdr
import shutil
import subprocess

class io:
    
    @staticmethod
    def makeDirs(path, mode=0777):
        '''
        Will attempt to make the full directory structure, if it doesn't exist, for the supplied 'path'
        
        Exceptions
        ==========
        OSError: if the directory cannot be created
        '''
        if not os.path.exists(path):
            os.makedirs(path, mode)
    
    @staticmethod
    def rmTree(path, ignore_errors=False, onerror=None):
        '''
        Will attempt to make the full directory structure, if it doesn't exist, for the supplied 'path'
        
        Exceptions
        ==========
        OSError: if the directory cannot be created
        '''
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors, onerror)
            
    @staticmethod
    def writeToFile(contents, writePath, writeMode="w"):
        '''
        Writes the supplied 'contents' to the file at the specified 'writePath'
        The file will be closed after writing
        
        Exceptions
        ==========
        IOError: if the file cannot be opened
        '''
        f = open(writePath, writeMode)
        f.write(contents)
        f.close()
        
    @staticmethod
    def invokeCommandSync(cmdArgs, error, message):
        '''
        Invokes a process/function on the command line
        
        Exceptions
        ==========
        Raises the passed in "error" if an exception occurs
        '''
        proc = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        if proc.returncode != 0:
            print(output)
            raise error, message
        
        return output
    
class image:
    
    @staticmethod
    def isImage(filePath):
        '''
        Returns a boolean indicating if the filePath points at an image
        '''
        return os.path.isfile(filePath) and imghdr.what(filePath) != None
    
    @staticmethod
    def imageListFromDir(imageDir, sortKey=None, reverse=False):
        '''
        Takes a directory and returns a list of image paths.
        Can optionally provide sort options (sortKey for the method to sort by, and reverse to specify the direction)
        By default the list is sorted alphabetically.
        '''
        allImages = []
        for fileName in os.listdir(imageDir):
            filePath = os.path.join(imageDir, fileName)
            
            if image.isImage(filePath): 
                allImages.append(filePath)
        return sorted(allImages, key=sortKey, reverse=reverse)
    
class translate:
    
    @staticmethod
    def map(origDict, keyMap, preserve=False):
        '''
        Used to map a dictionary.
        The keyMap is a dictionary which maps old key names to the new key name {old: new}.
        If the preserved option is set to True, for any key that exists in origDict but isn't mapped, the original key will be used.
        If the preserved option is set to False, for any key that exists in origDict but isn't mapped, it will be omitted from the returned dictionary
        
        Returns a new dictionary containing the new keys.
        '''
        removeKey = "***NO KEY FOUND - REMOVE***" 
        newDict = dict([(keyMap.get(key, key if preserve else removeKey), value) for key, value in origDict.iteritems()])
        if removeKey in newDict:
            del newDict[removeKey]
        return newDict
    
    @staticmethod
    def weave(flagDict):
        '''
        Converts a dictionary of command line flags into a list
        
        Returns the new flag list
        '''
        flagList = []
        [(flagList.append(key), flagList.append(value)) for key, value in flagDict.iteritems()]
        return flagList