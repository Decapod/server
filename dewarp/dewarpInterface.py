import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

# Exception classes
class DewarpError(Exception): pass

def dewarpPair(calibrationDir, dewarpedPath, img1, img2):

    # Invokes the dewarping command
    executable = os.path.join("..", "..", "decapod-dewarping", "dewarp.py")
    cmd = [executable, calibrationDir, img1, img2, dewarpedPath]
    utils.io.invokeCommandSync(cmd, DewarpError, "Error at dewarping")
