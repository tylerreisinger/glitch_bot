import Glitch.Events.Event

class PlayerEnterEvent(Glitch.Events.Event.Event):
    def __init__(self, player):
        super(PlayerEnterEvent, self).__init__()
        self._player = player
        
    @property
    def Player(self):
        return self._player
    
class PlayerLeaveEvent(Glitch.Events.Event.Event):
    def __init__(self, player, location):
        super(PlayerLeaveEvent, self).__init__()
        self._player = player
        self._location = location
        
    @property
    def Player(self):
        return self._player
    
    @property
    def Location(self):
        return self._location
        
class BuffRemovedEvent(Glitch.Events.Event.Event):
    def __init__(self, buff):
        self._buff = buff
        
    @property
    def Buff(self):
        return self._buff
    
class BuffAddedEvent(Glitch.Events.Event.Event):
    def __init__(self, buff):
        self._buff = buff
        
    @property
    def Buff(self):
        return self._buff