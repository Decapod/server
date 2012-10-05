import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils
from status import Status
from store import FSStore

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_READY = "ready"
EXPORT_ERROR = "error"

# Exception classes
class DewarpError(Exception): pass
class DewarpInProgressError(Exception): pass

class Dewarp(object):
    
    def __init__(self, dataDir, statusFile):
        self.dataDir = dataDir
        self.unpacked = os.path.join(self.dataDir, "unpacked")
        self.dewarped = os.path.join(self.dataDir, "dewarped")
        self.statusFilePath = statusFile

        self.setupExportFileStructure()
        self.status = Status(FSStore(self.statusFilePath), {"status": EXPORT_READY})  

    def setupExportFileStructure(self):
        '''
        Sets up the directory structure and initializes the status
        '''
        utils.io.makeDirs(self.dataDir)

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):        
        return self.status.model
    
    def dewarp(self, file):
        '''
        Generates the pdf export.
        If an exception is raised from the genPDF subprocess the status will be set to EXPORT_ERROR
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        PageImagesNotFoundError: if no page images are provided for the pdf generation
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            # perform dewarp, update status including percentage complete
            pass
    
    def delete(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.dataDir)
            self.setupExportFileStructure()
            self.status.update("status", EXPORT_READY)
            self.status.remove("percentage")
