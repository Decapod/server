
class Firer(object):
    def __init__(self):
        self.listeners = {}

    def addListener(self, name, listener):
        self.listeners[name] = listener

    def removeListener(self, name):
        del self.listeners[name]

    def fire(self, *args, **kwargs):
        for listener in self.listeners.values():
            listener(*args, **kwargs)

    def __len__(self):
        return len(self.listeners)
