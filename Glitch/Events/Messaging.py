'''
Created on Apr 17, 2012

@author: tyler
'''

from Glitch.Events.Event import Event

class RoomOpenedEvent(Event):
    def __init__(self, room, success):
        self._roomId = room
        self._success = success
        
    @property
    def Success(self):
        return self._success
    
    @property
    def RoomId(self):
        return self._roomId

class RoomMessageEvent(Event):        
    def __init__(self, packetObj):
        self._text = packetObj[u'txt']
        self._roomId = packetObj[u'tsid']
        self._playerId = packetObj[u'pc'][u'tsid']
        self._playerName = packetObj[u'pc'][u'label']
        
    @property
    def Text(self):
        return self._text
    
    @property
    def RoomId(self):
        return self._roomId
    
    @property
    def PlayerId(self):
        return self._playerId
    
    @property
    def PlayerName(self):
        return self._playerName
    
class LocalMessageEvent(Event):
    def __init__(self, packetObj):
        self._text = packetObj[u'txt']
        self._playerId = packetObj[u'pc'][u'tsid']
        self._playerName = packetObj[u'pc'][u'label']
        
    @property
    def Text(self):
        return self._text
    
    @property
    def PlayerId(self):
        return self._playerId
    
    @property
    def PlayerName(self):
        return self._playerName
        