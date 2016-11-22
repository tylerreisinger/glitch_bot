from Glitch.Events.Messaging import RoomOpenedEvent

class ChatManager(object):
    def __init__(self, globalId, helpId):
        self._globalId = globalId
        self._helpId = helpId
        self._openRooms = []
        
    def SendLocalChatMessage(self, client, message):
        return client.SendPacket('local_chat', {'txt' : message})
    
    def OpenRoom(self, client, roomId):
        return client.SendPacket('groups_chat_join', {'tsid' : roomId}, callbackFn = self._ChatJoinCallback, callbackArgs = (client, roomId))
    
    def IsRoomOpen(self, roomId):
        for room in self._openRooms:
            if room == roomId:
                return room
        return None
    
    @property
    def OpenRooms(self):
        return self._openRooms
    
    @property
    def GlobalId(self):
        return self._globalId
    
    @property
    def LiveHelpId(self):
        return self._helpId
    
    def _ChatJoinCallback(self, packetEvent, client, groupId):
        if packetEvent.packetObject[u'success'] == True:
            self._openRooms.append(groupId)
        event = RoomOpenedEvent(groupId, packetEvent.eventObject[u'success'])
        client.QueueEvent(event)
            