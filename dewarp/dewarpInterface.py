import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

DEWARP_PREFIX = "dewarped"

# Exception classes
class DewarpError(Exception): pass

def dewarpPair(calibrationDir, dewarpedPath, img1, img2):

    # Invokes the dewarping command
    # TODO: Need to update the path when the location of dewarp.py is determined
    executable = os.path.join("..", "..", "..", "..", "decapod-dewarping", "dewarp.py")
    cmd = [executable, calibrationDir, img1, img2, DEWARP_PREFIX]
    utils.io.invokeCommandSync(cmd, DewarpError, "Error at dewarping")
