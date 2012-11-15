import sys
import os
import shutil

MOCK_DATA_DIR = os.path.abspath("mockData/")

def calibrate(imagePath, calibratePath):
    mockCalibrationDir = os.path.join(MOCK_DATA_DIR, "calibration")
    
    srcFiles = os.listdir(mockCalibrationDir)
    for fileName in srcFiles:
        fullFileName = os.path.join(mockCalibrationDir, fileName)
        if (os.path.isfile(fullFileName)):
            shutil.copy(fullFileName, calibratePath)
