import os
import sys

import cameraInterface

class Cameras(object):
    
    def __init__(self, test=False):
        self.cameraController = cameraInterface if not test else None
    
    def getCamerasSummary(self):
        return self.cameraController.getAllCamerasSummary()
