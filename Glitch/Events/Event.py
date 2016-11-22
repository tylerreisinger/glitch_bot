class Event(object):
    def __init__(self):
        self._userData = None
        self._msgId = None
        
    @property
    def UserData(self):
        return self._userData
    
    @property
    def MessageId(self):
        return self._msgId
    
    
        
class PacketEvent(Event):
    def __init__(self, packetObj):
        self.packetObject = packetObj
        Event.__init__(self)
    
    @property
    def Type(self):
        return self.packetObject[u'type']
    
class LoginCompleteEvent(Event):
    def __init__(self):
        Event.__init__(self)
    
class ShutdownEvent(Event):
    def __init__(self):
        Event.__init__(self)
    
class ReloginStartEvent(Event):
    def __init__(self):
        Event.__init__(self)
        
class ReloginEndEvent(Event):
    def __init__(self):
        Event.__init__(self)