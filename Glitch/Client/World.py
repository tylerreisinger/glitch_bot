from Glitch.Events.Item import VerbQueryEvent, VerbActionEvent
import Glitch.Events.WorldEvents
import Glitch.Events.Player
from Glitch.Client.Player import Player

import json

class Location(object):
    def __init__(self, locationId, name):
        self._id = locationId
        self._name = name
                
    @property
    def Id(self):
        return self._id
    
    @property
    def Name(self):
        return self._name
    
class WorldLocation(Location):
    def __init__(self, locationId, name, moteId, hubId, moteName = None, hubName = None):
        super(WorldLocation, self).__init__(locationId, name)
        self._moteId = moteId
        self._hubId = hubId
        self._moteName = moteName
        self._hubName = hubName
        
    @property
    def MoteId(self):
        return self._modeId
    
    @property
    def HubId(self):
        return self._hubId
    
    @property
    def MoteName(self):
        return self._moteName
    
    @property
    def HubName(self):
        return self._hubName
    
def _CreateLocationFromObject(obj):
    name = None
    tsid = None
    if u'tsid' in obj:
        tsid = obj[u'tsid']
    elif u'street_tsid' in obj:
        tsid = obj[u'street_tsid']
    if u'label' in obj:
        name = obj[u'label']
    elif u'name' in obj:
        name = obj[u'name']
    if u'mote_id' in obj:
        moteName = None
        if u'mote_name' in obj:
            moteName = obj[u'mote_name']
        hubName = None
        if u'hub_name' in obj:
            hubName = obj[u'hub_name']
        return WorldLocation(tsid, name, obj[u'mote_id'], obj[u'hub_id'], moteName, hubName)
    else:
        return Location(tsid, name)

class GroundEntity(object):
    def __init__(self, obj):
        self._x = obj[u'x']
        self._y = obj[u'y']
        self._classId = obj[u'class_tsid']
        self._path = obj[u'path_tsid'].split('/')
        self._label = None
        self._count = obj[u'count']
        self._s = None
        if u's' in obj:
            self._s = obj[u's']
        if u'label' in obj:
            self._label = obj[u'label']
            
    def QueryVerbList(self, client, data = None):
        return client.SendPacket('itemstack_verb_menu', {'starting_menu' : True, 'itemstack_tsid' : self.Id}, callbackFn = self._QueryVerbListCallback, callbackArgs = (client,), userData = data)
        
    def DoVerb(self, client, verb, count = 1, extraArgs = {}, data = None):
        args = {'itemstack_tsid' : self.Id, 'count' : count, 'verb' : verb}
        args.update(extraArgs)
        return client.SendPacket('itemstack_verb', args, callbackFn = self._DoVerbCallback, callbackArgs = (client, verb), userData = data)
        
    @property
    def ClassId(self):
        return self._classId
    
    @property
    def Id(self):
        return self._path[len(self._path) - 1]
    
    @property
    def ParentContainerId(self):
        if len(self._path) > 1:
            return self._path[len(self._path) - 2]
        return None
    
    @property
    def XPosition(self):
        return self._x
    
    @property
    def YPosition(self):
        return self._y
    
    @property
    def Label(self):
        return self._label
    
    @property
    def Count(self):
        return self._count
    
    @property
    def S(self):
        return self._s
    
    def _Update(self, obj):
        if u'x' in obj:
            self._x = obj[u'x']
        if u'y' in obj:
            self._y = obj[u'y']
        if u'class_tsid' in obj:
            self._classId = obj[u'class_tsid']
        if u'path_tsid' in obj:
            self._path = obj[u'path_tsid'].split('/')
        if u'label' in obj:
            self._label = obj[u'label']
        if u'count' in obj:
            self._count = obj[u'count']
        if u's' in obj:
            self._s = obj[u's']
            
    def _QueryVerbListCallback(self, packet, client):
        event = VerbQueryEvent(packet.packetObject[u'itemDef'], self)
        client.QueueEvent(event)
        
    def _DoVerbCallback(self, packet, client, verb):
        event = VerbActionEvent(packet.packetObject, self, verb)
        client.QueueEvent(event)
        
class VerbState(object):
    def __init__(self, enabled, warning, disabledReason):
        self._enabled = enabled
        self._warning = warning
        self._disabledReason = disabledReason
        
    @property
    def Enabled(self):
        return self._enabled
    
    @property
    def HasWarning(self):
        return self._warning
    
    @property
    def DisabledReason(self):
        return self._disabledReason
        
        
class VerbStateEntity(GroundEntity):
    def __init__(self, obj):
        super(VerbStateEntity, self).__init__(obj)
        self._rookVerbs = None
        self._tendVerbs = None
        self._verbStates = {}
        if u'status' in obj:
            if u'is_rook_verbs' in obj[u'status']:
                self._rookVerbs = obj[u'status'][u'is_rook_verbs']
            if u'is_tend_verbs' in obj[u'status']:
                self._tendVerbs = obj[u'status'][u'is_tend_verbs']
            if u'verb_states' in obj[u'status']:
                for k, v in obj[u'status'][u'verb_states'].iteritems():
                    self._verbStates[k]= VerbState(v[u'enabled'], v[u'warning'], v[u'disabled_reason'])
                
    @property
    def IsRookVerbs(self):
        return self._rookVerbs
    
    @property
    def IsTendVerbs(self):
        return self._tendVerbs
    
    @property
    def VerbStates(self):
        return self._verbStates
    
    def _Update(self, obj):
        super(VerbStateEntity, self)._Update(obj)
        if u'status' in obj:
            if u'is_rook_verbs' in obj[u'status']:
                self._rookVerbs = obj[u'status'][u'is_rook_verbs']
            if u'is_tend_verbs' in obj[u'status']:
                self._tendVerbs = obj[u'status'][u'is_tend_verbs']
        if u'verb_states' in obj:
            for k, v in obj[u'status'][u'verb_states']:
                self._verbStates[k] = VerbState(v[u'enabled'], v[u'warning'], v[u'disabled_reason'])
        
class TreeEntity(VerbStateEntity):
    def __init__(self, obj):
        super(TreeEntity, self).__init__(obj)
        self._health = obj[u's'][u'h']
        self._maturity = obj[u's'][u'm']
        self._fruitAmount = obj[u's'][u'f_num']
        self._fruitMax = obj[u's'][u'f_cap']
        
    @property
    def Health(self):
        return self._health
    
    @property
    def Maturity(self):
        return self._maturity
    
    @property
    def FruitQuantity(self):
        return self._fruitAmount
    
    @property
    def FruitMax(self):
        return self._fruitMax
    
    def _Update(self, obj):
        super(TreeEntity, self)._Update(obj)
        if u's' in obj and isinstance(obj[u's'], dict):
            if u'h' in obj[u's']:
                self._health = obj[u's'][u'h']
            if u'm' in obj[u's']:
                self._health = obj[u's'][u'm']
            if u'f_num' in obj[u's']:
                self._fruitAmount = obj[u's'][u'f_num']
            if u'f_cap' in obj[u's']:
                self._fruitMax = obj[u's'][u'f_cap']
                
class StorageDepositBoxEntity(GroundEntity):
    def __init__(self, obj):
        super(StorageDepositBoxEntity, self).__init__(obj)
        if u'config' in obj and u'special_display' in obj[u'config']:
            self._storageCount = 0
            if u'item_count' in obj[u'config'][u'special_display'][0]:
                self._storageCount = obj[u'config'][u'special_display'][0][u'item_count']
            self._storageItem = None
            if u'item_class' in obj[u'config'][u'special_display'][0]:
                self._storageItem = obj[u'config'][u'special_display'][0][u'item_class']
        self._slots = obj[u'slots']
        
    @property
    def StorageItem(self):
        return self._storageItem
    
    @property
    def StorageCount(self):
        return self._storageCount
    
    @property
    def Slots(self):
        return self._slots
    
    def _Update(self, obj):
        super(StorageDepositBoxEntity, self)._Update(obj)
        if u'config' in obj and u'special_display' in obj[u'config']:
            sdObj = obj[u'config'][u'special_display'][0]
            if u'item_count' in sdObj:
                self._storageCount = sdObj[u'item_count']
            if u'item_class' in sdObj:
                self._storageCount = sdObj[u'item_class']
        if u'slots' in obj:
            self._slots = obj[u'slots']
            
        
def MakeGroundEntity(obj):
    if obj[u'class_tsid'] == 'bag_furniture_sdb':
        return StorageDepositBoxEntity(obj)
    if u's' in obj and isinstance(obj[u's'], dict) == True and u'h' in obj[u's']:
        return TreeEntity(obj)
    elif u'status' in obj:
        return VerbStateEntity(obj)
    else:
        return GroundEntity(obj)
    
class Door(object):
    def __init__(self, doorId, obj):
        self._id = doorId
        self._x = obj[u'x']
        self._y = obj[u'y']
        self._keyId = None
        if u'key_id' in obj:
            self._keyId = obj[u'key_id']
        self._destination = _CreateLocationFromObject(obj[u'connect'])
        
    def Enter(self, client):
        return client.SendPacket('door_move_start', {'from_door_tsid': self.Id}, callbackFn = self._MoveStart, callbackArgs = (client,))
    
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
    def KeyId(self):
        return self._keyId
    
    @property
    def Destination(self):
        return self._destination
    
    def _MoveStart(self, packet, client):
        client._HandleMoveStart(packet.packetObject, 'door')

class Signpost(object):
    def __init__(self, signpostId, obj):
        self._targetLocations = {}
        if u'connects' in obj:
            for k, v in obj[u'connects'].iteritems():
                self._targetLocations[k] = (WorldLocation(v[u'street_tsid'], v[u'label'], v[u'mote_id'], v[u'hub_id']))
        self._x = obj[u'x']
        self._y = obj[u'y']
        self._id = signpostId
        
    def MoveTo(self, client, locationIndex):
        client.SendPacket('signpost_move_start', {'from_signpost_tsid': self._id, 'destination_index': locationIndex}, callbackFn = self._SignpostMoveStart, callbackArgs = (client, locationIndex))
    
    def ContainsLocationId(self, locationId):
        for location in self._targetLocations.itervalues():
            if location.Id == locationId:
                return location
            
    def ContainsLocationName(self, locationName):
        for location in self._targetLocations.itervalues():
            if location.Name == locationName:
                return location    
    
    def GetTargetIndexById(self, locationId):
        for k, v in self._targetLocations.iteritems():
            if v.Id == locationId:
                return k
        return None
    
    def GetTargetIndexByName(self, locationName):
        for k, v in self._targetLocations.iteritems():
            if v.Name == locationName:
                return k
        return None
    
    @property
    def Id(self):
        return self._id
    
    @property
    def TargetLocations(self):
        return self._targetLocations
    
    @property
    def XPosition(self):
        return self._x
    
    @property
    def YPosition(self):
        return self._y
    
    def _SignpostMoveStart(self, packet, client, targetId):
        oldLocation = client._activeLocation
        if packet.packetObject[u'success']:
            if u'hostport' in packet.packetObject:
                client._ReloginOnDisconnect(packet.packetObject[u'hostport'][:packet.packetObject[u'hostport'].find(':')], packet.packetObject[u'token'], 'signpost', oldLocation, True)
            else:
                event = Glitch.Events.WorldEvents.MoveStartEvent(packet.packetObject, client._activeLocation)
                client._LocationChange(packet.packetObject[u'location']) 
                client.QueueEvent(event)
                client.SendPacket('signpost_move_end', {'destination_index': targetId, 'from_signpost_tsid': self._id}, callbackFn = self._SignpostMoveEnd, callbackArgs = (client, oldLocation))
        else:
            event = Glitch.Events.WorldEvents.MoveStartEvent(packet.packetObject, client._activeLocation)
            client.QueueEvent(event)
            
    def _SignpostMoveEnd(self, packet, client, oldLocation):
        event = Glitch.Events.WorldEvents.MoveEndEvent(packet.packetObject, oldLocation)
        if packet.packetObject[u'success']:
            client._activeLocation._MoveEnd(packet.packetObject[u'location'])
        client.QueueEvent(event)
        
        
class MapRegion(object):
    def __init__(self, obj):
        self._streets = []
        self._name = obj[u'name']
        if 'streets' in obj:
            for k, v in obj[u'streets'].iteritems():
                self._streets.append(Location(k, v))
                
    @property
    def Name(self):
        return self._name
    
    @property
    def Streets(self):
        return self._streets

class MapData(object):
    def __init__(self, obj):
        self._regions = []
        if u'all' in obj:
            for region in obj[u'all'].itervalues():
                self._regions.append(MapRegion(region))
                
    def GetLocationIdByName(self, streetName, regionName = None):
        if regionName:
            for region in self._regions:
                if region.Name == regionName:
                    for street in region.Streets:
                        if street.Name == streetName:
                            return street.Id
                    break
            return None
        else:
            for region in self._regions:
                for street in region.Streets:
                    if street.Name == streetName:
                        return street.Id
            return None
        
    def GetRegionByName(self, regionName):
        for region in self._regions:
            if region.Name == regionName:
                return region
    
    @property
    def Regions(self):
        return self._regions
    
class ActiveLocation(WorldLocation):
    def __init__(self, obj):
        super(ActiveLocation, self).__init__(obj[u'tsid'], obj[u'mapInfo'][u'name'], obj[u'mapInfo'][u'mote_id'], obj[u'mapInfo'][u'hub_id'], obj[u'mapInfo'][u'mote_name'], obj[u'mapInfo'][u'hub_name'])
        self._groundY = obj[u'ground_y']
        self._sources = []
        if u'sources' in obj:
            for source in obj[u'sources']:
                self._sources.append(source)
                
        self._signPosts = []
        self._doors = []
        self._mapData = None
        
        if u'layers' in obj:
            for layer in obj[u'layers'].itervalues():
                if u'signposts' in layer:
                    for k, v in layer[u'signposts'].iteritems():
                        self._signPosts.append(Signpost(k, v))
                if u'doors' in layer:
                    for k, v in layer[u'doors'].iteritems():
                        self._doors.append(Door(k, v))
        
        self._entities = []
        
        self._players = []
        
        if u'mapData' in obj and obj[u'mapData'] != None:
            self._mapData = MapData(obj[u'mapData'])
        
    def GetPathToLocation(self, client, locationId):
        return client.SendPacket('get_path_to_location', {'loc_tsid': locationId}, callbackFn = self._GetPathToLocationHandler, callbackArgs = (client,))
        
    def GetEntityById(self, entityId):
        for entity in self._entities:
            if entity.Id == entityId:
                return entity
    
    def GetEntitiesByClassId(self, *args):
        entities = []
        for entity in self._entities:
            for classId in args:
                if entity.ClassId == classId:
                    entities.append(entity)
        return entities
    
    def GetEntitesByLabel(self, label):
        entities = []
        for entity in self._entities:
            if entity.Label == label:
                entities.append(entity)
        return entities
    
    def CountEntitesByClassId(self, classId):
        count = 0
        for entity in self._entities:
            if entity.classId == classId:
                count += entity.count
        return count
    
    def CountEntitiesByLabel(self, label):
        count = 0
        for entity in self._entities:
            if entity.Label == label:
                count += entity.count
        return count
    
    def GetPlayerById(self, tsid):
        for player in self._players:
            if player.Id == tsid:
                return player
            
    def GetPlayerByName(self, name):
        for player in self._players:
            if player.Name == name:
                return player
            
    def GetSignpostContainingLocationId(self, locationId):
        for sign in self._signPosts:
            for location in sign.TargetLocations.itervalues():
                if location.Id == locationId:
                    return sign
        return None
    
    def GetSignpostContainingLocationName(self, locationName):
        for sign in self._signPosts:
            for location in sign.TargetLocations.itervalues():
                if location.Name == locationName:
                    return sign
        return None
                
    @property
    def GroundY(self):
        return self._groundY
    
    @property
    def Sources(self):
        return self._sources
    
    @property
    def Signposts(self):
        return self._signPosts
    
    @property
    def Doors(self):
        return self._doors
    
    @property
    def Entities(self):
        return self._entities
    
    @property
    def Players(self):
        return self._players
    
    @property
    def MapData(self):
        return self._mapData
    
    @property
    def Trees(self):
        trees = []
        for entity in self._entities:
            if entity.ClassId.find('_') != -1:
                if entity.ClassId.split('_')[0] == 'trant':
                    trees.append(entity)
        return trees
    
    def _GetPathToLocationHandler(self, packet, client):
        event = Glitch.Events.WorldEvents.GetPathToLocationEvent(packet.packetObject)
        client.QueueEvent(event)
    
    def _MoveEnd(self, obj):
        if u'itemstacks' in obj:
            for v in obj[u'itemstacks'].itervalues():
                self._entities.append(MakeGroundEntity(v))
        if u'pcs' in obj:
            for player in obj[u'pcs'].itervalues():
                self._players.append(Player(player))
                
    def _PlayerMoved(self, playerId, x, y):
        player = self.GetPlayerById(playerId)
        if player:
            player._x = x
            player._y = y
            
    def _HandlePcMove(self, client, packetObj):
        if u'pc' in packetObj:
            tsid = packetObj[u'pc'][u'tsid']
            if self.GetPlayerById(tsid) != None:
                if packetObj[u'pc'][u'location'][u'tsid'] != self.Id:
                    count = 0
                    for player in self._players:
                        if player.Id == tsid:
                            client.QueueEvent(Glitch.Events.Player.PlayerLeaveEvent(player, _CreateLocationFromObject(packetObj[u'pc'][u'location'])))
                            del self._players[count]
                            print("Player " + player.Id + " left.")
                            break
                        count += 1
                else:
                    print("INFO: Player move received with player in same location.")
            else:
                player = Player(packetObj[u'pc'])
                self._players.append(player)
                print("New player in location " + packetObj[u'pc'][u'tsid'])
                client.QueueEvent(Glitch.Events.Player.PlayerEnterEvent(player))
                
    def _UpdateEntites(self, obj):
        for k, v in obj.iteritems():
            entity = self.GetEntityById(k)
            if entity != None:
                if u'class_tsid' in v and v[u'class_tsid'] == 'DELETED':
                    self._entities.remove(entity)
                else:
                    entity._Update(v)
            elif u'class_tsid' in v and v[u'class_tsid'] != 'DELETED':
                if u'class_tsid' in v:
                    if u'x' not in v:
                        #print("Something bizzare happened!")
                        #errorLog = open('/home/tyler/GlitchPacketLogs/Errors', 'w')
                        #errorLog.write(json.dumps(v, indent=3) + '\n')
                        #errorLog.close()
                        #print(v)
                        continue
                    entity = MakeGroundEntity(v)
                    self._entities.append(entity)