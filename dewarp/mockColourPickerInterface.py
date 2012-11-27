import os
import sys

sys.path.append(os.path.abspath(os.path.join('..', 'utils')))
import utils

def launchColourPicker(img):

    # Invokes the colourPicker command
    writePath = os.path.join(os.getcwd(), ".colors")
    utils.io.writeToFile("55 24 21\n5 5 4", writePath)
