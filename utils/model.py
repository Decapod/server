from events import Events

def getSegs(elPath):
    '''
    Takes in a string of path segment or a list of path segments.
    Returns a list of path segments.
    '''
    return elPath.split(".") if isinstance(elPath, str) else elPath

def getImp(dictionary, segs):
    '''
    Takes in a dictionary object to search in and a list of path segments into it.
    Will return the value at the path or None if it doesn't exist.
    '''
    seg = segs.pop(0)
    segVal = dictionary.get(seg)
    
    if len(segs) > 0 and segVal is not None:
        return getImp(segVal, segs)
    else:
        return segVal

def setImp(dictionary, segs, value):
    '''
    Takes in a dictionary object and a list of path segments into it.
    Will set the value at the specified path, and will create intermediate segments if they do not currently exist.
    Note that this will convert path segments to dictionaries if they currently are not.
    '''
    seg = segs.pop(0)

    if len(segs) > 0:
        dictionary.setdefault(seg, {})
        setImp(dictionary[seg], segs, value)
    else:
        dictionary[seg] = value
        
def get(dictionary, elPath):
    '''
    Takes in a dictionary object to search in and an elPath (string with . separated path segments, or list of path segments) into it.
    Will return the value at the path or None if it doesn't exist.
    '''
    return getImp(dictionary, getSegs(elPath))

def set(dictionary, elPath, value):
    '''
    Takes in a dictionary object and an elPath (string with . separated path segments, or list of path segments) into it.
    Will set the value at the specified path, and will create intermediate segments if they do not currently exist.
    Note that this will convert path segments to dictionaries if they currently are not.
    '''
    setImp(dictionary, getSegs(elPath), value)
                   
class ChangeApplier(object):
    def __init__(self, dictionary):
        self.model = dictionary
        self.onModelChanged = Events()
             
    def requestUpdate(self, elPath, value):
        '''
        Takes in an elPath into the change appliers model reference, and sets the value on it.
        Fires the onModelChanged event with newModel, oldModle,and request
        '''
        origModel = self.model.copy()
        set(self.model, elPath, value)
        self.onModelChanged.fire(newModel=self.model, oldModel=origModel, request={"elPath": elPath, "value": value, "type": "UPDATE"})
    
    def requestRemoval(self, elPath):
        '''
        Takes in an elPath into the change appliers model and removes it.
        Fires the onModelChanged event with newModel, oldModle,and request
        If there is nothing to remove, no event will be fired.
        '''
        origModel = self.model.copy()
        segs = getSegs(elPath)
        key = segs.pop()
        parent = self.model if len(segs) == 0 else get(self.model, segs)
        
        if parent is not None and key in parent:
            del parent[key]
            self.onModelChanged.fire(newModel=self.model, oldModel=origModel, request={"elPath": elPath, "type": "REMOVAL"})
