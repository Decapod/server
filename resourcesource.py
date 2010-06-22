
import os
import json

serverBasePath = os.path.dirname(os.path.abspath(__file__))

class ResourceSource(object):
    resources = {}
    
    def __init__(self, configPath):
        configFile = open(configPath)
        self.resources = json.load(configFile)
    
    def filePath(self, resourceName):
        if resourceName in self.resources:
            return serverBasePath + self.resources[resourceName]["source"]
        else:
            return None
        
    def webURL(self, resourceName):
        if resourceName in self.resources:
            return self.resources[resourceName]["target"]
        else:
            return None
    
    def cherryPyConfig(self):
        config = {}
        
        # Create CherryPy static resource mount config entries for each resource.
        for resource in self.resources.values():
            config[resource["target"]] = {
                "tools.staticdir.on": True,
                "tools.staticdir.dir": resource["source"]
            }
        
        # Define the server's base path    
        config["/"] = {
            "tools.staticdir.root": serverBasePath
        }
        
        return config;
