import sys
import os
import shutil

MOCK_DATA_DIR = os.path.abspath("mockData/")

def dewarpPair(calibrationDir, dewarpoedPath, img1, img2):
    imgDir = os.path.join(MOCK_DATA_DIR)
    
    shutil.copyfile(os.path.join(imgDir, "capture-0_1.jpg"), os.path.join(dewarpoedPath, "capture-0_1.jpg"))
    shutil.copyfile(os.path.join(imgDir, "capture-0_2.jpg"), os.path.join(dewarpoedPath, "capture-0_2.jpg"))
