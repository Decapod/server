import os
import sys
import re
from string import Template

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import dewarpInterface
import mockDewarpInterface
import utils
from status import Status
from store import FSStore

#constants for statuses
EXPORT_IN_PROGRESS = "in progress"
EXPORT_COMPLETE = "complete"
EXPORT_READY = "ready"
EXPORT_ERROR = "error"

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

# Exception classes
class DewarpError(Exception): pass
class DewarpInProgressError(Exception): pass
class UnpackedDirNotExistError(Exception): pass

class DewarpProcessor(object):
    
    def __init__(self, dataDir, statusFile, testmode=False):
        self.dataDir = dataDir
        self.unpackedDir = os.path.join(self.dataDir, "unpacked")
        self.dewarpedDir = os.path.join(self.dataDir, "dewarped")
        self.calibrationDir = os.path.join(self.unpackedDir, "calibration")
        self.export = os.path.join(self.dataDir, "export.zip")
        self.statusFilePath = statusFile
        self.dewarpController = mockDewarpInterface if testmode else dewarpInterface

        utils.io.makeDirs(self.dataDir)
        self.status = Status(FSStore(self.statusFilePath), {"status": EXPORT_READY})  

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):        
        return self.status.model
    
    def getArchiveStatus(self, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        if not os.path.exists(self.unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(self.unpackedDir)
        
        if not os.path.exists(self.calibrationDir):
            return self.constructErrorStatus("CalibrationDirNotExist", "The calibration directory \"{0}\" does not exist.".format(self.calibrationDir))

        matched, unmatched = self.findPairs(self.unpackedDir, filenameTemplate)
        
        if unmatched:
            return self.constructErrorStatus("UnmatchedPairs", ''.join(unmatched))
        
        return self.constructSucessStatus(len(matched))
    
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
            utils.io.rmTree(self.dewarpedDir)
            self.status.update("status", EXPORT_READY)
            self.status.remove("percentage")

    def deleteUpload(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.unpackedDir)

    def unzip(self, file, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Unzips the uploaded archive and returns a dict of status.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping currently in progress, cannot accept another zip until this process has finished"
        
        utils.io.unzip(file, self.unpackedDir)
        
        return self.getArchiveStatus(filenameTemplate)
        
    def dewarp(self):
        '''
        Generates the pdf export.
        If an exception is raised from the genPDF subprocess the status will be set to EXPORT_ERROR
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        DewarpError: if unable to complete dewarping 
        '''
        
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping currently in progress, cannot accept another zip until this process has finished"
        else:
            # perform dewarp, update status including percentage complete
            self.status.update("status", EXPORT_IN_PROGRESS)
            try:
                self.dewarpImp(self.unpackedDir, self.dewarpedDir)
            except Exception as e:
                self.status.update("status", EXPORT_ERROR)
                self.status.remove("percentage")
                utils.io.rmTree(self.dewarpedDir)
                
                raise DewarpError, e.message
            
            self.status.update("status", EXPORT_COMPLETE)
    
    def dewarpImp(self, unpackedDir, dewarpedDir, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Dewarps the paired images in the from directory "unpackedDir" and output to "dewarpedDir"
        
        The "unpackedDir" contains all the paired images and the calibration information
        The "dewarpedDir" is the output directory of all the dewarped images. It will be created if it does not exist.
        
        Exceptions:
        ==========
        UnpackedDirNotExistError: If the directory for the unpacked dewarping zip does not exist
        '''
        
        if not os.path.exists(unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(unpackedDir)
        
        matched, unmatched = self.findPairs(unpackedDir, filenameTemplate)
        
        if matched:
            if not os.path.exists(dewarpedDir):
                os.mkdir(dewarpedDir)
                
            self.status.update("percentage", 0)
            numOfMatches = len(matched)
            
            for index, (img1, img2) in enumerate(matched):
                self.dewarpController.dewarpPair(self.calibrationDir, dewarpedDir, img1, img2)
                self.status.update("percentage", int((index+1)/numOfMatches*100))
    
        return True
    
    def findPairs(self, unpackedDir, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        unmatched = []
        matched = []
        
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex="\d*")
        allImages = utils.image.findImages(unpackedDir, regexPattern, False)
        
        sortedAllImages = sorted(allImages)
        
        # find the maximum captureIndex
        while len(sortedAllImages) > 0:
            currentImg = sortedAllImages.pop(0)
            
            imgPrefix, theRest = currentImg.split("_")
            
            if imgPrefix and theRest:
                imgMatchPattern = "^" + imgPrefix
                regex = re.compile(imgMatchPattern)
                
                numOfImages = len(sortedAllImages)
                
                if numOfImages > 0 and regex.findall(sortedAllImages[0]):
                    pairImg = sortedAllImages[0]
                
                    # Toss out the pair image to prevent the further comparison
                    sortedAllImages.pop(0)
                    matched.append((currentImg, pairImg))
                else:
                    unmatched.append(currentImg)
            else:
                unmatched.append(currentImg)
                
        return matched, unmatched
    
    def constructErrorStatus(self, errorCode, msg):
        return {"ERROR_CODE": errorCode, "msg": msg}

    def constructSucessStatus(self, numOfCaptures):
        return {"numOfCaptures": numOfCaptures}
    