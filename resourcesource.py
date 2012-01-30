import os
import cherrypy

def parseVirtualPath(virtualPath):
    '''
    Parses a tokenized path into a tuple containing the script name and path.
    Will throw an exception if there is no leading token provided.
    
    Example virtual path "${token}/path/"
    '''
    tokens = virtualPath.split("/", 1)
    resourceToken = tokens[0]
    path = tokens[1] if len(tokens) > 1 else ""
    if resourceToken.startswith("${") and resourceToken.endswith("}"):
        parsed = resourceToken[2:-1]
        return os.path.join("/", parsed), path
    else:
        raise Exception

def cpurl(path='', qs='', script_name=None, base=None, relative=None):
    '''
    Passes straight through to cherrypy.url
    This is just a convenience to offer the full range of cherrypy.url options 
    that are captured by in the url fucntion.
    '''
    return cherrypy.url(path, qs, script_name, base, relative)

def url(virtualPath):
    '''
    Converts a virtual path into an appropriate web url
    '''
    script_name, path = parseVirtualPath(virtualPath)
    if not cherrypy.request.app and path != "":
        path = os.path.join("/", path)
    return cherrypy.url(path, script_name=script_name)

def path(virtualPath, absolute=True, config=None):
    '''
    Converts a virtual path into a filesystem path.
    
    Note 1: that the paths will use cherrypy's config, or a supplied config for conversions.
    '''
    script_name, path = parseVirtualPath(virtualPath)
    static_dir = "tools.staticdir.dir"
    config_dict = config if config else cherrypy.request.app.config
    section = config_dict[script_name][static_dir]
    fspath = os.path.join(section, path)
    return os.path.join(os.getcwd(), fspath) if absolute else fspath
