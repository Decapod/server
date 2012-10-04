import os
import re
import imghdr
import shutil
import subprocess
import uuid
import simplejson as json
from zipfile import ZipFile

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
        Will attempt to remove the full directory structure
        
        Exceptions
        ==========
        OSError: if the directory cannot be removed
        '''
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors, onerror)
    
    @staticmethod
    def rmFile(path):
        if os.path.exists(path):
            os.remove(path)
    
    @staticmethod
    def writeToFile(contents, writePath, writeMode="w"):
        '''
        Writes the supplied 'contents' to the file at the specified 'writePath'
        The file will be closed after writing
        
        Exceptions
        ==========
        IOError: if the file cannot be opened
        '''
        io.makeDirs(os.path.dirname(writePath))
        
        f = open(writePath, writeMode)
        f.write(contents)
        f.close()
    
    @staticmethod
    def readFromFile(filePath):
        if not os.path.isfile(filePath): return None
        
        f = open(filePath)
        content = f.read()
        f.close()
        
        return content

    @staticmethod  
    def loadJSONFile(jsonFile):
        '''
        Reads in a json file and returns a python dictionary
        
        Exceptions
        ==========
        IOError: if the jsonFile doens't exists
        JSONDecodeError: from simplejson, if the file is not in proper json format
        '''
        jFile = open(jsonFile)
        d = json.load(jFile)
        jFile.close()
        return d

    @staticmethod
    def writeToJSONFile(jsonData, jsonFile):
        '''
        Writes json data to a file.
        It will replace the contents of the file with the passed in json data.
        
        Exceptions
        ==========
        IOError: if there is an error writing to the file
        TypeError: from simplejson, if the jsonData is not JSON serializable
        '''
        io.writeToFile(json.dumps(jsonData), jsonFile)
    
    @staticmethod    
    def zip(dirPath, fileName):
        '''
        Creates a zipfile with all of the contents in the directory at the end of the path.
        It will walk down and recursively add in all subdirectories and their contents.
        
        Note that the directory structure of the path will also be created. If you do not
        want this to happen, make sure the function is called in the top most directory 
        that you want in the zip with the path as "."
        '''
        
        zFile = ZipFile(fileName, mode="w")
        
        for path, dirs, files in os.walk(dirPath):
            for file in files:
                zFile.write(os.path.join(path, file))
        
        zFile.close()
        
    @staticmethod
    def invokeCommandSync(cmdArgs, error, message, waitForRtn=True):
        '''
        Invokes a process/function on the command line
        
        Exceptions
        ==========
        Raises the passed in "error" if an exception occurs
        '''
        proc = subprocess.Popen(cmdArgs, stdout=subprocess.PIPE)
        
        if waitForRtn:
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
    def findImages(dir, regexPattern=None):
        '''
        Finds all of the images that match the regexPattern in the list of dirs.
        If no regexPattern is provided, it will find all images.
        '''
         
        imagePaths = []
        regex = re.compile(regexPattern) if regexPattern else None
        
        for path, dirs, files in os.walk(dir):
            for file in files: 
                filePath = os.path.join(path, file)
                fitsPattern = True if not regex else regex.findall(filePath)
                
                if image.isImage(filePath) and fitsPattern:
                    imagePaths.append(filePath)
                    
        return imagePaths 
    
    @staticmethod
    def removeImages(dir, regexPattern=None):
        '''
        Removes all of the images that match the regexPattern in the list of dirs.
        If no regexPattern is provided, it will remove all images.
        '''
        
        imagePaths = image.findImages(dir, regexPattern)
        for imagePath in imagePaths:
            os.remove(imagePath)

        return imagePaths
    
    @staticmethod
    def generateImageName(prefix="decapod-", suffix="jpeg"):
        '''
        Creates a unique name for the image file using the passed in prefix, suffix, and a generated uuid
        '''
        id = uuid.uuid4()
        return "{0}{1}.{2}".format(prefix, id.hex, suffix)
    
    @staticmethod
    def getImageType(filePath):
        return imghdr.what(filePath)

    @staticmethod
    def renameWithExtension(filePath, fileName=None):
        path, basename = os.path.split(filePath)
        splitBasename = basename.split(".")
        base = splitBasename.pop(0)
        
        if splitBasename:
            splitBasename[-1] = image.getImageType(filePath)
        else:
            splitBasename.append(image.getImageType(filePath))

        splitBasename.insert(0, base)
        newName = os.path.join(path, ".".join(splitBasename))
        os.rename(filePath, newName)
        return newName
     
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
    
class server:
    
    @staticmethod
    def setJSONResponseHeaders(cherrypy, fileName="model.json"):
        '''
        Sets the JSON Response headers that will be returned by the server
        '''
        cherrypy.response.headers["Content-Type"] = "application/json"
        cherrypy.response.headers["Content-Disposition"] = "attachment; filename='{0}'".format(fileName)

    @staticmethod
    def getURL(cherrypy, filePath, serverRootPath, baseURL=None):
        '''
        Converts the absolute path of a physical file to a web-accessible URL
        The 4th parameter "baseURL" is only needed for unit tests
        '''
        base = cherrypy.request.base if baseURL is None else baseURL
        return filePath.replace(serverRootPath, base)
    
class conversion:
    
    @staticmethod
    def convertStrToFunc(module, funcName):
        '''
        Converts a string of function name in a moduel into a function object
        @param:
        module: A module object
        funcName: string of a function name in the module
        '''
        
        return reduce(getattr, funcName.split("."), module)
        