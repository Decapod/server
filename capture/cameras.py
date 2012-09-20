import os
import sys

import cameraInterface
import mockCameraInterface

class Cameras(object):
    
    def __init__(self, test=False):
        self.cameraController = cameraInterface if not test else mockCameraInterface
    
    def getCamerasSummary(self):
        return self.cameraController.getAllCamerasSummary()
