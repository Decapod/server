import os
import simplejson as json
import utils

# Exception classes
class StatusTypeError(Exception): pass
class StatusFormatError(Exception): pass

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

class status(object):
    
    def __init__(self, statusFile, defaultState="ready"):
        self.statusFile = statusFile
        self.status = {"status": defaultState}
        
        self.setupStatusFile()
        
    def __str__(self):
        return json.dumps(self.status)
        
    def setupStatusFile(self):
        '''
        Ensures that the status file is present. 
        If it already exists, it will read it in and set the status with it.
        '''
        if not os.path.exists(self.statusFile):
            self.set(self.status)
        else:
            self.status = loadJSONFile(self.statusFile)
    
    def updateStatusFile(self):
        '''
        Meant for internal use to write the status out to the status file, 
        but can be used externally if updating the status dictionary directly
        '''
        utils.io.writeToFile(str(self), self.statusFile)
    
    def set(self, status):
        '''
        Completely replaces the status with the new dictionary passed in.
        
        Exceptions
        ==========
        StatusTypeError: if the passed in status is not a dictionary
        '''
        if not isinstance(status, dict):
            raise StatusTypeError("{0} should be an instance of 'dict'".format(status))
        if "status" not in status:
            raise StatusFormatError("The 'status' key is missing")
        self.status = status
        self.updateStatusFile()
    
    def update(self, status):
        '''
        Updates the status file with from another dictionary (or any other form that a dictionary's update function takes)
        It will overwrite any duplicate keys with the new value passed in
        '''
        self.status.update(status)
        self.updateStatusFile()
        
    def delKey(self, key):
        '''
        Removes a single key and it's value from the status file
        '''
        del self.status[key]
        self.updateStatusFile()
        
    def inState(self, state):
        '''
        Returns a boolean indicating if it is currently in the provided state
        '''
        return self.status["status"] == state

