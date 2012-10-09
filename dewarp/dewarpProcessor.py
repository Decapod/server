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
class UnzipError(Exception): pass
class DewarpInProgressError(Exception): pass
class UnpackedDirNotExistError(Exception): pass
class CalibrationDirNotExistError(Exception): pass
class UnmatchedPairsError(Exception): pass

class DewarpProcessor(object):
    
    def __init__(self, dataDir, statusFile, testmode=False):
        self.dataDir = dataDir
        self.unpacked = os.path.join(self.dataDir, "unpacked")
        self.dewarped = os.path.join(self.dataDir, "dewarped")
        self.export = os.path.join(self.dataDir, "export.zip")
        self.statusFilePath = statusFile
        self.dewarpController = mockDewarpInterface if testmode else dewarpInterface

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

    def dewarp(self, file):
        '''
        Generates the pdf export.
        If an exception is raised from the genPDF subprocess the status will be set to EXPORT_ERROR
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        PageImagesNotFoundError: if no page images are provided for the pdf generation
        '''
        
        try:
            utils.io.unzip(file, self.unpacked)
        except Exception:
            raise UnzipError, "Cannot unzip \"{0}\"".format(file)
        
        if self.isInState(EXPORT_IN_PROGRESS):
            raise DewarpInProgressError, "Export currently in progress, cannot generated another pdf until this process has finished"
        else:
            # perform dewarp, update status including percentage complete
            self.status.update("status", EXPORT_IN_PROGRESS)
            self.dewarpImp(self.unpacked, self.dewarped)
            self.status.update("status", EXPORT_COMPLETE)
    
    def dewarpImp(self, unpackedDir, dewarpedDir, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Dewarps the paired images in the from directory "unpackedDir" and output to "dewarpedDir"
        
        The "unpackedDir" contains all the paired images and the calibration information
        The "dewarpedDir" is the output directory of all the dewarped images. It will be created if it does not exist.
        
        Exceptions:
        ==========
        UnpackedDirNotExistError: If the directory for the unpacked dewarping zip does not exist
        UnmatchedPairsError: If there are unmatched pairs in the image set for dewarping
        CalibrationDirNotExistError: If the calibration directory does not exist
        '''
        
        if not os.path.exists(unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(unpackedDir)
        
        matched, unmatched = self.findPairs(unpackedDir, filenameTemplate)
        
        if unmatched:
            raise UnmatchedPairsError, ''.join(unmatched)
        
        if matched:
            calibrationDir = os.path.join(unpackedDir, "calibration")
            
            if not os.path.exists(calibrationDir):
                raise CalibrationDirNotExistError, "The calibration directory \"{0}\" does not exist.".format(calibrationDir)
            
            if not os.path.exists(dewarpedDir):
                os.mkdir(dewarpedDir)
                
            self.status.update("percentage", 0)
            numOfMatches = len(matched)
            
            for index, (img1, img2) in enumerate(matched):
                try:
                    self.dewarpController.dewarpPair(calibrationDir, dewarpedDir, img1, img2)
                except Exception:
                    self.status.update("status", EXPORT_ERROR)
                    raise DewarpError, "Failed to dewarp the image pair ({0}, {1})".format(img1, img2)
                
                self.status.update("percentage", int((index+1)/numOfMatches*100))
    
        return True
    
    def findPairs(self, unpackedDir, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        unmatched = []
        matched = []
        
        regexPattern = Template(filenameTemplate).safe_substitute(cameraID="\d*", captureIndex="\d*")
        allImages = utils.image.findImages(unpackedDir, regexPattern, False)
        
        sortedAllImages = sorted(allImages)
        
        # find the maxium captureIndex
        while len(sortedAllImages) > 0:
            currentImg = sortedAllImages.pop(0)
            
            imgPrefix, theRest = currentImg.split("_")
            
            if imgPrefix is None or theRest is None:
                continue
            
            imgMatchPattern = "^" + imgPrefix
            regex = re.compile(imgMatchPattern) if regexPattern else None
            
            if regex:
                numOfImages = len(sortedAllImages)
                
                if numOfImages > 0: 
                    pairImg = sortedAllImages[0] if regex.findall(sortedAllImages[0]) else None
                
                # Toss out the pair image to prevent the furthur comparison
                if numOfImages and pairImg is not None:
                    sortedAllImages.pop(0)
                    matched.append((currentImg, pairImg))
                else:
                    unmatched.append(currentImg)
        
        return matched, unmatched