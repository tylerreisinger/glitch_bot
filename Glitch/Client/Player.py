from Glitch.Client.Inventory import Inventory
import Glitch.Events.WorldEvents
import Glitch.Client.World

import time

class Group(object):
    def __init__(self, groupId, groupObj):
        self._groupId = groupId
        self._name = groupObj[u'name']
        self._ownsProperty = groupObj[u'owns_property']
    
    @property
    def Id(self):
        return self._groupId
    
    @property
    def Name(self):
        return self._name

    @property
    def OwnsProperty(self):
        return self._ownsProperty
    
class Player(object):
    def __init__(self, obj):
        self._id = obj[u'tsid']
        self._x = obj[u'x']
        self._y = obj[u'y']
        self._isAdmin = None
        if u'is_admin' in obj:
            self._isAdmin = obj[u'is_admin']
        self._isGuide = None
        if u'is_guide' in obj:
            self._isGuide = obj[u'is_guide']
        self._name = obj[u'label']
        self._level = obj[u'level']
        self._online = obj[u'online']
        self._location = Glitch.Client.World._CreateLocationFromObject(obj[u'location'])
        self._home = None
        self._homeStreet = None
        
        for street in obj[u'home_info'].itervalues():
            if street[u'label'].find('House') != -1:
                self._home = Glitch.Client.World._CreateLocationFromObject(street)
            elif street[u'label'].find('Street') != -1:
                self._homeStreet = Glitch.Client.World._CreateLocationFromObject(street)
                
    @property
    def Id(self):
        return self._id
    
    @property
    def XPosition(self):
        return self._x
    
    @property
    def YPosition(self):
        return self._y
    
    @property
    def IsAdmin(self):
        return self._isAdmin
    
    @property
    def IsGuide(self):
        return self._isGuide
    
    @property
    def Name(self):
        return self._name
    
    @property
    def Level(self):
        return self._level
    
    @property
    def IsOnline(self):
        return self._online
    
    @property
    def Location(self):
        return self._location
    
    @property
    def Home(self):
        return self._home
    
    @property
    def HomeStreet(self):
        return self._homeStreet
    
class Buff(object):
    def __init__(self, obj, buffId = None):
        self._isDebuff = obj[u'is_debuff']
        self._name = obj[u'name']
        self._id = buffId
        if u'tsid' in obj:
            self._id = obj[u'tsid']
        self._duration = obj[u'duration']
        self._ticks = obj[u'ticks']
        self._description = obj[u'desc']
        
        self._remainingDuration = self._duration
        if u'remaining_duration' in obj:
            self._remainingDuration = u'remaining_duration'
        self._ticksElapsed = 0
        if u'ticks_elapsed' in obj:
            self._ticksElapsed = obj[u'ticks_elapsed']
        self._itemClass = None
        if u'item_class' in obj:
            self._itemClass = obj[u'item_class']
        
        self._createTime = time.time()
        
    def TimeLeft(self):
        return self._remainingDuration - (time.time() - self._createTime)
        
    @property
    def Id(self):
        return self._id
    
    @property
    def Name(self):
        return self._name
    
    @property
    def IsDebuff(self):
        return self._isDebuff
    
    @property
    def Duration(self):
        return self._duration
    
    @property
    def Ticks(self):
        return self._ticks
    
    @property
    def Description(self):
        return self._description       
    
    @property
    def ItemClass(self):
        return self._itemClass 
    
    @property   
    def TicksElapsed(self):
        return self._ticksElapsed

class LocalPlayer(object):
    def __init__(self, pcId, playerObject):
        self._inventory = Inventory(playerObject[u'pc'][u'itemstacks'])
        self._id = pcId
        self._stats = playerObject[u'pc'][u'stats']
        self._x = playerObject[u'pc'][u'x']
        self._y = playerObject[u'pc'][u'y']
        self._groups = []
        self._buffs = []
        
        self._teleportLocations = {}
        self._teleportEnergyCost = 0
        self._teleportTokenCount = 0
        self._tokensUsed = 0
        self._tokensMax = 0
        self._freeTeleportsUsed = 0
        self._freeTeleportsMax = 0
        self._teleportLevel = 0
        
        
        if u'groups' in playerObject:
            for k, v in playerObject[u'groups'].iteritems():
                self._groups.append(Group(k, v))
                
        if u'buffs' in playerObject:
            for k, v in playerObject[u'buffs'].iteritems():
                self._buffs.append(Buff(v, k))
                
    def GetBuffById(self, buffId):
        for buff in self._buffs:
            if buff.Id == buffId:
                return buff
            
    def GetBuffByName(self, name):
        for buff in self._buffs:
            if buff.Name == name:
                return buff
    
    def InGroup(self, groupId = None, name = None):
        if groupId:
            for group in self._groups:
                if groupId == group.Id:
                    return True
        elif name:
            for group in self._groups:
                if name == group.Name:
                    return True
        return False
    
    def GetGroupById(self, groupId):
        for group in self._groups:
                if groupId == group.Id:
                    return group
    
    def GetGroupByName(self, name):
        for group in self._groups:
            if name == group.Name:
                return group
            
    def MoveTo(self, client, x, y, s = "7"):
        client.SendPacket('move_xy', {'x' : x, 'y': y, 's': s}, False)
        
    def GoHome(self, client):
        client.SendPacket('local_chat', {'txt':'/home'})
        
    def LeaveHome(self, client):
        client.SendPacket('local_chat', {'txt': '/leave'})
        
    def Teleport(self, client, teleportId):
        locationId = None
        if teleportId in self._teleportLocations:
            locationId = self._teleportLocations[teleportId]
        client.SendPacket('teleportation_go', {'teleport_id': teleportId}, callbackFn = self._TeleportCallback, callbackArgs = (client, locationId))
    
    def MapTeleport(self, client, locationId, useToken = False):
        client.SendPacket('teleportation_map', {'loc_tsid': locationId, 'is_token': useToken}, callbackFn = self._TeleportCallback, callbackArgs = (client, locationId))
    
    @property
    def XPosition(self):
        return self._x
    
    @property
    def YPosition(self):
        return self._y
    
    @property
    def TeleportLocations(self):
        return self._teleportLocations
    
    @property
    def TeleportEnergyCost(self):
        return self._teleportEnergyCost
    
    @property
    def TeleportTokenCount(self):
        return self._teleportTokenCount
    
    @property
    def TeleportTokensUsed(self):
        return self._tokensUsed
    
    @property
    def TeleportTokensMax(self):
        return self._tokensMax
    
    @property
    def FreeTeleportsUsed(self):
        return self._freeTeleportsUsed
    
    @property
    def FreeTeleportsMax(self):
        return self._freeTeleportsMax
    
    @property
    def TeleportationLevel(self):
        return self._teleportLevel
    
    @property
    def Groups(self):
        return self._groups
    
    @property
    def Inventory(self):
        return self._inventory
    
    @property
    def Buffs(self):
        return self._buffs
    
    @property
    def Id(self):
        return self._id
    
    @property
    def Currants(self):
        return self._stats[u'currants']
    
    @property
    def QuoinsToday(self):
        return self._stats[u'quoins_today'][u'value']
    
    @property
    def QuoinsMax(self):
        return self._stats[u'quoins_today'][u'max']
    
    @property
    def XpGainedToday(self):
        return self._stats[u'xp_gained_today']
    
    @property
    def Energy(self):
        return self._stats[u'energy'][u'value']
    
    @property
    def EnergyMax(self):
        return self._stats[u'energy'][u'max']
    
    @property
    def Mood(self):
        return self._stats[u'mood'][u'value']
    
    @property
    def MoodMax(self):
        return self._stats[u'mood'][u'max']
    
    @property
    def Level(self):
        return self._stats[u'level']
    
    @property
    def IsSubscriber(self):
        return self._stats[u'is_subscriber']
    
    @property
    def XpTotal(self):
        return self._stats[u'xp'][u'total']
    
    @property
    def XpNext(self):
        return self._stats[u'xp'][u'nxt']
    
    @property
    def XpBase(self):
        return self._stats[u'xp'][u'base']
    
    @property
    def Favor(self):
        return self._stats[u'favor_points']
    
    @property
    def EnergySpentToday(self):
        return self._stats[u'energy_spent_today']
    
    def _RemoveBuff(self, client, buffId):
        buff = self.GetBuffById(buffId)
        if buff:
            self._buffs.remove(buff)
            client.QueueEvent(Glitch.Events.Player.BuffRemovedEvent(buff))
            
    def _AddBuff(self, client, buffObj):
        buff = Buff(buffObj)
        self._buffs.append(buff)
        client.QueueEvent(Glitch.Events.Player.BuffAddedEvent(buff))
        
    def _UpdateBuff(self, client, buffObj):
        buff = self.GetBuffById(buffObj[u'tsid'])
        if buff == None:
            print("ERROR: buff_update on non-existent buff!")
            return
        if u'duration' in buffObj:
            buff._duration = buffObj[u'duration']
        if u'remaining_duration' in buffObj:
            buff._remainingDuration = buffObj[u'remaining_duration']
            buff._createTime = time.time()
    
    def _TeleportCallback(self, packet, client, location):
        event = Glitch.Events.WorldEvents.TeleportEvent(packet.packetObject, location)
        client.QueueEvent(event)
    
    def _TeleportUpdate(self, packetObj):
        if u'teleportation' in packetObj:
            if u'targets' in packetObj[u'teleportation']:
                for k, v in packetObj[u'teleportation'][u'targets'].iteritems():
                    self._teleportLocations[int(k)] = Glitch.Client.World._CreateLocationFromObject(v)
            self._teleportEnergyCost = packetObj[u'teleportation'][u'energy_cost']
            self._teleportTokenCount = packetObj[u'teleportation'][u'tokens_remaining']
            self._tokensUsed = packetObj[u'teleportation'][u'map_tokens_used']
            self._tokensMax = packetObj[u'teleportation'][u'map_tokens_max']
            self._freeTeleportsUsed = packetObj[u'teleportation'][u'map_free_used']
            self._freeTeleportsMax = packetObj[u'teleportation'][u'map_free_max']
            self._teleportLevel = packetObj[u'teleportation'][u'skill_level']
    
    def _StatsChange(self, statsObject):
        if u'mood' in statsObject:
            self._stats[u'mood'][u'value'] = statsObject[u'mood']
        if u'energy' in statsObject:
            self._stats[u'energy'][u'value'] = statsObject[u'energy']
        if u'xp' in statsObject:
            self._stats[u'xp'][u'total'] = statsObject[u'xp']
            
    def _MoveXY(self, x, y):
        if x:
            self._x = x
        if y:
            self._y = y