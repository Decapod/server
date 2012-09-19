from events import Events

def get(dictionary, elPath):
    '''
    Takes in a dictionary object to search in and an elPath (string with . separated path segments) into it.
    Will return the value at the path or None if it doesn't exist.
    '''
    segs = elPath.split(".")
    current = dictionary
    
    for seg in segs:
        if seg in current:
            current = current[seg]
        else:
            current = None
            break
    return current
    
def set(dictionary, elPath, value):
    '''
    Takes in a dictionary object and an elPath (string with . separated path segments) into it.
    Will set the value at the specified path, and will create intermediate segments if they do not currently exist.
    Note that this will convert path segments to dictionaries if they currently are not.
    '''
    
    segs = elPath.split(".")
    current = dictionary
    lastSegIndex = len(segs) - 1
    
    for index, seg in enumerate(segs):
        if not seg in current:
            current[seg] = {} 
        current[seg] = current[seg] if not index == lastSegIndex else value
        current = current[seg]
    

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
        '''
        origModel = self.model.copy()
        
        segs = elPath.split(".")
        if len(segs) > 1:
            path = segs[:-1].join(".")
            current = get(self.model, path)
            key = segs[-1]
            if key in current:
                del current[key]
        else:
            key = segs[0]
            if key in self.model:
                del self.model[key]
        
        self.onModelChanged.fire(newModel=self.model, oldModel=origModel, request={"elPath": elPath, "type": "REMOVAL"})
        
