from Glitch.Events.Event import Event
import Glitch.Client.World as World

class MoveStartEvent(Event):
    def __init__(self, packetObj, fromLocation):
        super(MoveStartEvent, self).__init__()
        if u'success' in packetObj:
            self._success = packetObj[u'success']
        else:
            self._success = True
        self._fromLocation = fromLocation
        self._toLocation = None
        if self._success:
            self._toLocation = World.WorldLocation(packetObj[u'location'][u'tsid'], packetObj[u'location'][u'mapInfo'][u'name'], packetObj[u'location'][u'mapInfo'][u'mote_id'], packetObj[u'location'][u'mapInfo'][u'hub_id'], packetObj[u'location'][u'mapInfo'][u'mote_name'], packetObj[u'location'][u'mapInfo'][u'hub_name'])
        
    @property
    def Success(self):
        return self._success
    
    @property
    def FromLocation(self):
        return self._fromLocation
    
    @property
    def ToLocation(self):
        return self._toLocation
    
class MoveEndEvent(Event):
    def __init__(self, packetObj, fromLocation):
        self._success = self._success = packetObj[u'success']
        self._fromLocation = fromLocation
        super(MoveEndEvent, self).__init__()
    
    @property
    def Success(self):
        return self._success
    
    @property
    def FromLocation(self):
        return self._fromLocation
    
class TeleportEvent(Event):
    def __init__(self, packetObject, fromLocation, toLocation):
        self._success = packetObject[u'success']
        self._fromLocation = fromLocation
        self._toLocation = toLocation
        super(TeleportEvent, self).__init__()
        
    @property
    def Success(self):
        return self._success
    
    @property
    def FromLocation(self):
        return self._fromLocation
    
    @property
    def ToLocation(self):
        return self._toLocation
    
class TeleportScriptUseEvent(Event):
    def __init__(self, packetObject, fromLocation, item):
        super(TeleportScriptUseEvent, self).__init__()
        self._item = item
        self._success = packetObject[u'success']
        self._fromLocation = fromLocation
        
    @property
    def Item(self):
        return self._item
    
    @property
    def Success(self):
        return self._success
    
    @property
    def FromLocation(self):
        return self._fromLocation
    
class GetPathToLocationEvent(Event):
    def __init__(self, packetObj):
        if u'path_info' in packetObj:
            self._path = packetObj[u'path_info'][u'path']
        self._success = packetObj[u'success']
        super(GetPathToLocationEvent, self).__init__()
        
    @property
    def Success(self):
        return self._success
    
    @property
    def Path(self):
        return self._path