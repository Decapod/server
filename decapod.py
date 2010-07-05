import sys
import cherrypy
import mockserver
import dserver

def parseServerName(serverName):
    pathSegs = serverName.split(".")
    assert 2, len(pathSegs)
    return pathSegs[0], pathSegs[1]

def readServerNameOption():
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return "dserver.DecapodServer"

def mountApp(moduleName, className = None):
    if className is None:
        moduleName, className = parseServerName(moduleName)
        
    serverModule = globals()[moduleName]
    rootClass = getattr(serverModule, className)
    root = rootClass()
    root.images = serverModule.ImageController(root.cameraSource)
    root.pdf = serverModule.Export()
    cherrypy.tree.mount(root, "/", serverModule.resources.cherryPyConfig())
    return root
        
def startServer():
    cherrypy.engine.start()
    
if __name__ == "__main__":
    mountApp(readServerNameOption())
    startServer()