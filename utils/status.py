import simplejson as json
from model import ChangeApplier

class Status(object):
    '''
    Manages a status dictionary and store.
    
    The store should be an instance of a class that has save and load methods,
    where the save method takes in a single argument of type dict and the load 
    takes no arguments and returns a dictionary.
    
    The model will default to an empty dict, you may provide an initialValue here or a 
    reference to a dict to use as a base. Note that this will not be copied, but modified
    directly.
    
    On changes to the model, through the update and remove methods, an event is fired to save 
    the store. You can add additional listeners by calling the addListener method on the instance's
    applier.onModelChanged property.
    '''
    
    def __init__(self, store, model={}):        
   
        self.store = store
        loaded = self.store.load()
        self.model = model
        
        if loaded:
            self.model.update(loaded)

        self.applier = ChangeApplier(self.model)
        self.applier.onModelChanged.addListener("internal.onSaveStatus", self.saveModel)
        
    def __str__(self):
        return json.dumps(self.model)
    
    def saveModel(self, newModel, oldModel, request):
        self.store.save(newModel)
        
    def update(self, elPath, value):
        self.applier.requestUpdate(elPath, value)
        
    def remove(self, elPath):
        self.applier.requestRemoval(elPath)