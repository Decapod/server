import os
import sys
import re

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import calibrateInterface
import mockCalibrateInterface
import utils
from status import Status
from store import FSStore

#constants for statuses
CALIBRATE_IN_PROGRESS = "in progress"
CALIBRATE_COMPLETE = "complete"
CALIBRATE_READY = "ready"
CALIBRATE_ERROR = "error"
REQUIRED_STEREO_IMAGES = 23

DEFAULT_CAPTURE_NAME_TEMPLATE = "capture-${captureIndex}_${cameraID}"

# Exception classes
class CalibrateError(Exception): pass
class CalibrateInProgressError(Exception): pass
class UnpackedDirNotExistError(Exception): pass

class Calibrator(object):
    
    def __init__(self, dataDir, statusFile, testmode=False):
        self.dataDir = dataDir
        self.unpackedDir = os.path.join(self.dataDir, "unpacked")
        self.calibrationDir = os.path.join(self.dataDir, "calibration")
        self.export = os.path.join(self.dataDir, "calibration.zip")
        self.statusFilePath = statusFile
        self.calibrateController = mockCalibrateInterface if testmode else calibrateInterface

        utils.io.makeDirs(self.dataDir)
        self.status = Status(FSStore(self.statusFilePath), {"status": CALIBRATE_READY})  

    def isInState(self, state):
        return self.status.model["status"] == state

    def getStatus(self):
        return self.status.model
    
    def getImagesStatus(self, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        if not os.path.exists(self.unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked captures zip does not exist.".format(self.unpackedDir)
        
        matched, unmatched = utils.image.findImagePairs(self.unpackedDir, filenameTemplate)
        
        actualStereoImages = len(matched)
        
        if actualStereoImages == 0:
            return self.constructErrorStatus("NO_STEREO_IMAGES", "Selected archive does not appear to have stereo images.")

        if actualStereoImages != REQUIRED_STEREO_IMAGES:
            return self.constructErrorStatus("NOT_ENOUGH_IMAGES", "Not enough calibration images are detected: Need {0} stereo images, found {1}.".format(REQUIRED_STEREO_IMAGES, actualStereoImages), 
                                             {"requiredStereoImages": REQUIRED_STEREO_IMAGES, "DetectedStereoImages": actualStereoImages})

        return self.constructSucessStatus(len(matched))
    
    def delete(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        CalibrateInProgressError: if calibration is currently in progress
        '''
        if self.isInState(CALIBRATE_IN_PROGRESS):
            raise CalibrateInProgressError, "Calibration in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.calibrationDir)
            utils.io.rmFile(self.export)
            self.status.update("status", CALIBRATE_READY)

    def deleteUpload(self):
        '''
        Removes the export artifacts.
        
        Exceptions
        ==========
        CalibrateInProgressError: if calibration is currently in progress
        '''
        if self.isInState(CALIBRATE_IN_PROGRESS):
            raise CalibrateInProgressError, "Calibration in progress, cannot delete until this process has finished"
        else:
            utils.io.rmTree(self.unpackedDir)

    def unzip(self, file, filenameTemplate=DEFAULT_CAPTURE_NAME_TEMPLATE):
        '''
        Unzips the uploaded archive and returns a dict of status.
        
        Exceptions
        ==========
        CalibrateInProgressError: if calibration is currently in progress
        '''
        
        if self.isInState(CALIBRATE_IN_PROGRESS):
            raise CalibrateInProgressError, "Calibration currently in progress, cannot accept another zip until this process has finished"
        
        fileType = utils.io.getFileType(file)
        
        if fileType != "zip":
            return self.constructErrorStatus("BAD_ZIP", "The zip file is invalid.")
        
        utils.io.rmTree(self.unpackedDir)
        
        name = file.filename if file.filename else utils.io.generateFileName(suffix=fileType)
        zipfilePath = os.path.join(self.dataDir, file.filename)
        utils.io.writeStreamToFile(file, zipfilePath)
        
        try:
            utils.io.unzip(zipfilePath, self.unpackedDir)
        except Exception:
            utils.io.rmFile(zipfilePath)
            return self.constructErrorStatus("BAD_ZIP", "The zip file is invalid.")
        
        utils.io.rmFile(zipfilePath)
        return self.getImagesStatus(filenameTemplate)
        
    def calibrate(self):
        '''
        Generates the calibration data export.
        If an exception is raised from the genPDF subprocess the status will be set to CALIBRATE_ERROR
        
        Exceptions
        ==========
        CalibrateInProgressError: if calibration is currently in progress
        CalibrateError: if unable to complete calibration 
        '''
        if not os.path.exists(self.unpackedDir):
            raise UnpackedDirNotExistError, "The directory \"{0}\" for the unpacked captures zip does not exist.".format(self.unpackedDir)
        
        if self.isInState(CALIBRATE_IN_PROGRESS):
            raise CalibrateInProgressError, "Calibration currently in progress, cannot accept another zip until this process has finished"
        else:
            # perform calibration, update status including percentage complete
            self.status.update("status", CALIBRATE_IN_PROGRESS)

            utils.io.rmTree(self.calibrationDir)
            utils.io.makeDirs(self.calibrationDir)
        
            try:
                self.calibrateController.calibrate(self.unpackedDir, self.calibrationDir)
            except Exception as e:
                self.status.update("status", CALIBRATE_ERROR)
                utils.io.rmTree(self.calibrationDir)
                
                raise CalibrateError, e.message
            
            currentDir = os.getcwd()
            os.chdir(self.dataDir)
            
            utils.io.zip("calibration", self.export)
            os.chdir(currentDir)
            
            self.status.update("status", CALIBRATE_COMPLETE)
    
    def constructErrorStatus(self, errorCode, msg, otherStatus = {}):
        basicStatus = {"ERROR_CODE": errorCode, "msg": msg}
        return dict(list(basicStatus.items()) + list(otherStatus.items()))

    def constructSucessStatus(self, numOfStereoImages):
        return {"numOfStereoImages": numOfStereoImages}
    