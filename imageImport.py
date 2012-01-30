import decapod_utilities as utils
import uuid
import os
import resourcesource

IMPORT_DIR = "${library}/book/images/"
imagePrefix = "decapod-"

class ImageImport(object):

    def __init__(self, resourcesource=resourcesource):
        self.rs = resourcesource
        self.importDir = self.rs.path(IMPORT_DIR)
                
        # Setup the import location.
        utils.mkdirIfNecessary(self.importDir)
    
    def generateImageName(self, prefix=imagePrefix, suffix="jpeg"):
        id = uuid.uuid4()
        return "{0}{1}.{2}".format(prefix, id.hex, suffix)
    
    def mimeToSuffix(self, mimeType):
        splitStr = mimeType.split('/')
        return splitStr[-1]
    
    def getFileType(self, file):
        mimeType = file.content_type.value
        return self.mimeToSuffix(mimeType)
    
    def writeFile(self, file, writePath):
        #Writes the file stream to disk at the path specified by writePath
        file.file.seek(0,0)
        fileData = file.file.read(8192)
        
        while fileData:
            saveFile = open(writePath, 'ab')
            saveFile.write(fileData)
            saveFile.close()
            fileData = file.file.read(8192)
        
        return writePath
    
    def save(self, file, name=None):
        # saves the file with the given name. 
        # if no name is provided it will call genearteImageName to create one
        fileType = self.getFileType(file)
        name = name if name else self.generateImageName(suffix=fileType)
        imagePath = os.path.join(self.importDir, name)
        
        return self.writeFile(file, imagePath)
