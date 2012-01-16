
import os
import json
import cherrypy

serverBasePath = os.path.dirname(os.path.abspath(__file__))

##########################
# Free utility functions #
##########################

def parseFileName (filePath):
    """Returns a tuple containing (file name, extension)."""
    lastSeg = filePath.rpartition("/")[2]
    splitName = lastSeg.partition(".")
    return (splitName[0], splitName[2])

def parsePathHead(filePath):
    return filePath.rpartition("/")[0] + "/"

def appendSuffix(filePath, suffix):
    fileName, extension = parseFileName(filePath)
    return parsePathHead(filePath) + fileName + suffix + "." + extension


##################
# ResourceSource #
##################

class ResourceSource(object):
    resources = {}
    
    def __init__(self, configPath):
        configFile = open(configPath)
        self.resources = json.load(configFile)
    
    def parseVirtualPath(self, virtualPath):
        if virtualPath == None:
            return None, None
        
        tokens = virtualPath.split("/")
        resourceToken = tokens[0]
        if resourceToken.startswith("${") == False or resourceToken.endswith("}") == False:
            return None, None
        
        return resourceToken[2:-1], tokens[1:]

    def virtualPath(self, absolutePath):
        if absolutePath is None:
            return None
        
        for resourceName in self.resources:
            resourcePath = self.filePathForResource(resourceName)
            if absolutePath.find(resourcePath) is 0:
                return absolutePath.replace(resourcePath, ("${%s}" % resourceName))
            
        return absolutePath
    
    def filePath(self, virtualPath):
        resourceName, pathSegs = self.parseVirtualPath(virtualPath)
        resourcePath = self.filePathForResource(resourceName)
        
        if resourceName == None or resourcePath == None:
            return None

        osPathSuffix = os.sep.join(pathSegs)    
        if osPathSuffix == "":
            return resourcePath
        else:
            return os.path.join(resourcePath, osPathSuffix)
        
    def webURL(self, virtualPath):
        tokenStart = virtualPath.find("${")
        tokenEnd = virtualPath.find("}")
        if tokenStart == -1 or tokenEnd == -1:
            return None
        
        resourceName = virtualPath[tokenStart + 2:tokenEnd]
        rest = virtualPath[tokenEnd + 1:]
        resourcePrefix = self.webURLForResource(resourceName)
        
        if resourcePrefix == None:
            return None
        else:
            return resourcePrefix + rest
    
    def filePathForResource(self, resourceName):
        if resourceName in self.resources:
            return os.path.join(serverBasePath, self.resources[resourceName]["source"])
        else:
            return None
    
    def webURLForResource(self, resourceName):
        if resourceName in self.resources:
            return self.resources[resourceName]["target"]
        else:
            return None
        
    def cherryPyConfig(self):
        config = {}
        
        # Create CherryPy static resource mount config entries for each resource.
        for resource in self.resources.values():
            target = resource["target"].encode('utf-8') # cherrypy 3.2.2 will crash if these are already unicode values.
            config[target] = {
                "tools.staticdir.on": True,
                "tools.staticdir.dir": resource["source"]
            }
        
        # Define the server's base path and dispatcher 
        config["/"] = {
            "tools.staticdir.root": serverBasePath,
            'request.dispatch': cherrypy.dispatch.MethodDispatcher()
        }
        
        return config;
