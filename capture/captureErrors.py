
ERROR_CODES = {
    "NO_CAMERAS": "No cameras detected", 
    "NO_CAPTURE": "Could not capture an image",
    "CAMERA_RESOLUTION_TOO_LOW": "Camera resolution is too low",
    "NO_MATCHING_PAIR": "The cameras are not matching",
    "TOO_MANY_CAMERAS": "Too many cameras detected",
    "CAMERA_DISCONECTED": "A Camera has been disconnected"
}

def generateErrorInfo(errorCode, **kwargs):
    '''
    Generates a dictionary with the error info.
    Can pass in keyword arguements for addiontal info to add to the dictionary
    '''
    errorInfo = {
        "errorCode": errorCode,
        "message": ERROR_CODES[errorCode]
    }
    errorInfo.update(kwargs)
    return errorInfo
