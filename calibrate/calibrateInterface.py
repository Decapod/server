import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

CHESSBOARD_WIDTH = 9
CHESSBOARD_HEIGHT = 6

# Exception classes
class CalibrateError(Exception): pass

def calibrate(imagePath, calibratePath):

    currentDir = os.getcwd()
    os.chdir(calibratePath)
    
    # Invokes the calibration command
    # TODO: Need to update the path when the location of calibrate.py is determined
    executable = os.path.join("..", "..", "..", "..", "..", "decapod-dewarping", "calibrate.py")
    cmd = [executable, imagePath, CHESSBOARD_WIDTH, CHESSBOARD_HEIGHT, calibratePath]
    utils.io.invokeCommandSync(cmd, None, None, False)
    
    os.chdir(currentDir)
