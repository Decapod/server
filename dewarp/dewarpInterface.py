import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

# Exception classes
class DewarpError(Exception): pass
class ColourValuesMissing(Exception): pass

def dewarpPair(calibrationDir, dewarpedPath, img1, img2):
    '''
    Exceptions
    ==========
    ColourValuesMissing: If the colours file is missing. This file holds the colours used by dewarping to identify the page separater and background.
    '''
    
    colourFile = os.path.join(os.getcwd(), ".colors")
    if not os.path.exists(colourFile):
        raise ColourValuesMissing, "The \"{0}\" file is missing.".format(colourFile)
    
    # Invokes the dewarping command
    executable = os.path.join("..", "..", "decapod-dewarping", "dewarp.py")
    cmd = [executable, calibrationDir, img1, img2, dewarpedPath]
    utils.io.invokeCommandSync(cmd, DewarpError, "Error at dewarping")
