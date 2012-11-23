import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

# Exception classes
class ColourPickerError(Exception): pass

def launchColourPicker(img):

    # Invokes the colourPicker command
    executable = os.path.join("..", "..", "decapod-dewarping", "colsel.py")
    cmd = [executable, img]
    utils.io.invokeCommandSync(cmd, ColourPickerError, "Error while running the colour picker")
