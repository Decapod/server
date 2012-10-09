import utils

# Exception classes
class DewarpError(Exception): pass

def dewarpPair(calibrationDir, dewarpedPath, img1, img2):

    cmd = ["dewarp.py", calibrationDir, img1, img2, dewarpedPath]

    output = utils.io.invokeCommandSync(cmd, DewarpError, "Failed to dewarp the image pair ({0}, {1})".format(cmd[2], cmd[3]))
    
    return output
