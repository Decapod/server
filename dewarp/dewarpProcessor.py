import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
sys.path.append(os.path.abspath(os.path.join('..', '..', 'decapod-dewarping')))
import dewarpInterface
import mockDewarpInterface
import utils
from status import Status
from store import FSStore
from calib import load

#constants for statuses
DEWARP_IN_PROGRESS = "in progress"
DEWARP_COMPLETE = "complete"
DEWARP_READY = "ready"
DEWARP_ERROR = "error"

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

# Exception classes
class DewarpError(Exception): pass
class DewarpInProgressError(Exception): pass
class UnpackedDirNotExistError(Exception): pass
class CalibrationDirNotExistError(Exception): pass

class DewarpProcessor(object):
    
    def __init__(self, dataDir, statusFile, testmode=False):
        self.dataDir = dataDir
        self.unpackedDir = os.path.join(self.dataDir, "unpacked")
        self.dewarpedDir = os.path.join(self.dataDir, "dewarped")
        self.calibrationDir = os.path.join(self.dataDir, "calibration")
        self.export = os.path.join(self.dataDir, "export.zip")
        self.statusFilePath = statusFile
        self.dewarpController = mockDewarpInterface if testmode else dewarpInterface

        utils.io.makeDirs(self.dataDir)
        self.status = Status(FSStore(self.statusFilePath), {"status": DEWARP_READY})  

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):
        return self.status.model
    
    def getCalibrationStatus(self):
        if not os.path.exists(self.calibrationDir):
            raise CalibrationDirNotExistError, "The directory \"{0}\" for the calibration zip does not exist.".format(self.calibrationDir)
        
        try:
            load(self.calibrationDir)
        except Exception:
            return self.constructErrorStatus("INVALID_CALIBRATION", "The calibration data is invalid.")
    
    def getCapturesStatus(self, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        if not os.path.exists(self.unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(self.unpackedDir)
        
        matched, unmatched = utils.image.findImagePairs(self.unpackedDir, filenameTemplate)
        
        if unmatched:
            return self.constructErrorStatus("UnmatchedPairs", map(os.path.basename, unmatched))
        
        return self.constructSucessStatus(len(matched))
    
    def delete(self):
        '''
        Removes the generated dewarped data and export artifacts.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.dewarpedDir)
            utils.io.rmFile(self.export)
            self.status.update("status", DEWARP_READY)
            self.status.remove("numOfCaptures")
            self.status.remove("currentCapture")

    def deleteCalibrationUpload(self):
        '''
        Removes the uploaded calibration data.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.calibrationDir)

    def deleteCapturesUpload(self):
        '''
        Removes the uploaded captures.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.unpackedDir)

    def unzipCalibration(self, file):
        '''
        Unzips the uploaded calibration archive.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping currently in progress, cannot accept another zip until this process has finished"
        
        self.deleteCalibrationUpload()
        self.delete()
        
        self.unzip(file, self.calibrationDir)
        return self.getCalibrationStatus()
    
    def unzipCaptures(self, file, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Unzips the uploaded captures archive.
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        '''
        
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping currently in progress, cannot accept another zip until this process has finished"
        
        self.deleteCapturesUpload()
        self.deleteCalibrationUpload()
        self.delete()
        
        self.unzip(file, self.unpackedDir)
        return self.getCapturesStatus(filenameTemplate)
    
    def unzip(self, file, outputDir):
        '''
        Unzips the uploaded archive.
        '''
        
        fileType = utils.io.getFileType(file)
        
        if fileType != "zip":
            return self.constructErrorStatus("BAD_ZIP", "The zip file is invalid.")
        
        name = file.filename if file.filename else utils.io.generateFileName(suffix=fileType)
        zipfilePath = os.path.join(self.dataDir, file.filename)
        utils.io.writeStreamToFile(file, zipfilePath)
            
        try:
            utils.io.unzip(zipfilePath, outputDir)
        except Exception:
            utils.io.rmFile(zipfilePath)
            return self.constructErrorStatus("BAD_ZIP", "The zip file is invalid.")
        
        utils.io.rmFile(zipfilePath)
        
    def dewarp(self):
        '''
        Dewarps and Generates the export of the dewarped images.
        If an exception is raised from the dewarp process the status will be set to DEWARP_ERROR
        
        Exceptions
        ==========
        DewarpInProgressError: if dewarping is currently in progress
        DewarpError: if unable to complete dewarping 
        '''
        
        if self.isInState(DEWARP_IN_PROGRESS):
            raise DewarpInProgressError, "Dewarping currently in progress, cannot accept another zip until this process has finished"
        else:
            # perform dewarp, update status including the current capture that's being processed
            self.status.update("status", DEWARP_IN_PROGRESS)
            try:
                self.dewarpImp(self.calibrationDir, self.unpackedDir, self.dewarpedDir)
            except Exception as e:
                self.status.update("status", DEWARP_ERROR)
                self.status.remove("numOfCaptures")
                self.status.remove("currentCapture")
                utils.io.rmTree(self.dewarpedDir)
                
                raise DewarpError, e.message
            
            currentDir = os.getcwd()
            os.chdir(self.dewarpedDir)
            
            utils.io.zip(".", self.export)
            os.chdir(currentDir)
            
            self.status.remove("numOfCaptures")
            self.status.remove("currentCapture")
            self.status.update("status", DEWARP_COMPLETE)
    
    def dewarpImp(self, calibrationDir, unpackedDir, dewarpedDir, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Dewarps the paired images in the from directory "unpackedDir" and output to "dewarpedDir"
        
        The "unpackedDir" contains all the paired images and the calibration information
        The "dewarpedDir" is the output directory of all the dewarped images. It will be created if it does not exist.
        
        Exceptions:
        ==========
        UnpackedDirNotExistError: If the directory for the unpacked dewarping zip does not exist
        CalibrationDirNotExistError: If the directory for the unpacked dewarping zip does not exist
        '''
        
        if not os.path.exists(calibrationDir):
            raise CalibrationDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(calibrationDir)
        
        if not os.path.exists(unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked dewarping zip does not exist.".format(unpackedDir)
        
        matched, unmatched = utils.image.findImagePairs(unpackedDir, filenameTemplate)
        
        if matched:
            if not os.path.exists(dewarpedDir):
                os.mkdir(dewarpedDir)
                
            numOfMatches = len(matched)
            self.status.update("numOfCaptures", numOfMatches)
            self.status.update("currentCapture", 0)
            
            for index, (img1, img2) in enumerate(matched):
                captureIndex = index + 1
                self.dewarpController.dewarpPair(calibrationDir, dewarpedDir, img1, img2)
                self.status.update("currentCapture", captureIndex)
    
        return True
    
    def constructErrorStatus(self, errorCode, msg):
        return {"ERROR_CODE": errorCode, "msg": msg}

    def constructSucessStatus(self, numOfCaptures):
        return {"numOfCaptures": numOfCaptures}
    