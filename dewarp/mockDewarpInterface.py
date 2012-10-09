import sys
import os
import shutil

MOCK_DATA_DIR = os.path.abspath("mockData/")

def dewarpPair(calibrationDir, dewarpedPath, img1, img2):
    imgDir = os.path.join(MOCK_DATA_DIR)
    
    shutil.copy(os.path.join(imgDir, "capture-0_1.jpg"), dewarpedPath)
    shutil.copy(os.path.join(imgDir, "capture-0_2.jpg"), dewarpedPath)
