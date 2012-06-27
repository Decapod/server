import os
import simplejson as json
import decapod_utilities as utils

class StatusTypeError(Exception): pass

class status(object):
    
    def __init__(self, statusFile):
        self.statusFile = statusFile
        self.status = {}
        
        self.setupStatusFile()
        
    def setupStatusFile(self):
        '''
        Ensures that the status file is present. 
        If it already exists, it will read it in and set the status with it.
        '''
        if not os.path.exists(self.statusFile):
            self.set(self.status)
        else:
            statusFile = open(self.statusFile)
            self.status = json.load(statusFile)
            statusFile.close()
    
    def updateStatusFile(self):
        '''
        Meant for internal use to write the status out to the status file, 
        but can be used externally if updating the status dictionary directly
        '''
        utils.writeToFile(self.getStatusString(), self.statusFile)
    
    def set(self, status):
        '''
        Completely replaces the status with the new dictionary passed in.
        
        Raises a StatusTypeError if the passed in status is not a dictionary
        '''
        if not isinstance(status, dict):
            raise StatusTypeError("{0} should be an instance of 'dict'".format(status))
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
    
    def getStatusString(self):
        '''
        Returns the serialized status dictionary
        '''
        return json.dumps(self.status)

