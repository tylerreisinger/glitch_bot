from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.Item
import Glitch.Events.Player

import threading

class AnimalHarvestClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, regions, actions, log = None):
        super(AnimalHarvestClient, self).__init__(connectionFactory, pcId, log)
        
        self._streetsToVisit = []
        self._regions = regions
        self._path = []
        
        self._loot = {}
        self._locationsDone = []
        
        self._actions = []
        
        self._canEat = True
        
        self._animalsDepleted = {}
        self._currentAnimal = None
        
        self._timer = None
        
        self._verbCountMax = 0
        self._verbCount = 0
        self._verb = ''
        self._preVerb = True
    
    def _EventCallback(self, event):
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            if self.ActiveLocation.Name.find("House") != -1 or self.ActiveLocation.Name.find("Home") != -1:
                self.LocalPlayer.LeaveHome(self)
            else:
                for region in self._regions:
                    regionObject = self.ActiveLocation.MapData.GetRegionByName(region)
                    if regionObject:
                        self._streetsToVisit.extend(regionObject.Streets)
                self._meatCountInitial = self.LocalPlayer.Inventory.CountAllByClassId('meat')
                self.MoveToNext()
        
        elif isinstance(event, Glitch.Events.WorldEvents.GetPathToLocationEvent):
            if event.Success == True:
                self._path = event.Path
                self._path.reverse()
                self._path.pop()
                print("Got path to next location.")
                self.MoveToNext()
            else:
                print("Failed to get path to location!")
                self.Logout()
                self.StopSelf()
                return
            
        elif isinstance(event, Glitch.Events.WorldEvents.MoveEndEvent):
            print("Moved to " + self.ActiveLocation.Name + " from " + event.FromLocation.Name)
            if len(self.ActiveLocation.Players) > 0:
                print("Player found!")
                if not self.HandlePlayerFound():
                    self.Done()
                    return
            for location in self._streetsToVisit:
                if location.Id == self.ActiveLocation.Id:
                    self._streetsToVisit.remove(location)
                    print("Found " + str(len(self.ActiveLocation.GetEntitesByClassId('npc_piggy'))) + " pigs.")
                    self.NibbleOne()
                    return
            self.MoveToNext()
            
            if isinstance(event, Glitch.Events.Item.VerbActionEvent):
                if event.Success:
                    if event.Verb == self._verb:
                        self._verbCount += 1
                        if self._verbCount == self._verbCountMax:
                            if self._preVerb:
                                self._timer = threading.Timer(0.2, self.DoMainAction, (self._currentAnimal,))
                                self._timer.start()
                            else:
                                self.DoAction()
                    elif event.Verb == 'eat':
                        print("Eating complete.")
                        self._canEat = True
        
        elif isinstance(event, Glitch.Events.Player.PlayerEnterEvent):
            self.HandlePlayerFound()
        
        elif isinstance(event, Glitch.Events.Item.ItemAddedEvent):
            if event.Item.ClassId in self._loot:
                self._loot[event.Item.ClassId] += event.Item.Count
            else:
                self._loot[event.Item.ClassId] = event.Item.Count
            print("Gained " + str(event.Item.Count) + " units of " + event.Item.ClassId)
                
        elif isinstance(event, Glitch.Events.Item.ItemDeletedEvent):
            if event.Item.ClassId in self._loot:
                self._loot[event.Item.ClassId] -= event.Item.Count
            else:
                self._loot[event.Item.ClassId] = -event.Item.Count
            print("Lost " + str(event.Item.Count) + " units of " + event.Item.ClassId)
                
        elif isinstance(event, Glitch.Events.Item.ItemCountChangedEvent):
            delta = event.Item.Count - event.OldItemCount
            if event.Item.ClassId in self._loot:
                self._loot[event.Item.ClassId] += delta
            else:
                self._loot[event.Item.ClassId] = delta
            if delta > 0:
                print("Gained " + str(delta) + " units of " + event.Item.ClassId)
            else:
                print("Lost " + str(-delta) + " units of " + event.Item.ClassId)
                
                
    def MoveToNext(self):
        if len(self._path) > 0:
            location = self._path.pop()
            signpost = self.ActiveLocation.GetSignpostContainingLocationId(location)
            if signpost == None:
                print("No connecting signpost!")
                self.MoveToNext()
                return
            signpost.MoveTo(self, signpost.GetTargetIndexById(location))
        else:
            if len(self._streetsToVisit) > 0:
                self.ActiveLocation.GetPathToLocation(self, self._streetsToVisit[len(self._streetsToVisit) - 1].Id)
            else:
                self.Done()
                
    def DoAction(self):
        self.EatStuff()
        entities = self.ActiveLocation.GetEntitiesByClassId([action['entity_id'] for action in self._actions])
        
        for entity in entities:
            if entity not in self._animalsDepleted:
                self.LocalPlayer.MoveTo(self, entity.XPosition, entity.YPosition)
                print(entity.Id, 'X:', entity.XPosition, 'Y:', entity.YPosition)
                self._currentAnimal = entity
                self._timer = threading.Timer(0.4, self.DoPreAction, (entity,))
                self._timer.start()
                self._animalsDepleted[entity] = True
                return
            
        self.MoveToNext()
                
    def DoPreAction(self, entity):
        action = None
        for i in self._actions:
            if i['entity_id'] == entity.Id:
                action = i
        
        if action['preAction'] != None:
            print("Doing action", action['preAction'])
            self._verbCount = 0
            self._verbCountMax = action['preAction_count']
            self._verb = action['preAction']
            self._preVerb = True
            for i in range(0, action['preAction_count']):
                entity.DoVerb(self, action['preAction'], 1)
        else:
            self.DoMainAction(entity)
            
    def DoMainAction(self, entity):
        action = None
        for i in self._actions:
            if i['entity_id'] == entity.Id:
                action = i
        
        if action['mainAction'] != None:
            print("Doing action", action['mainAction'])
            self._verbCount = 0
            self._verbCountMax = action['mainAction_count']
            self._verb = action['mainAction']
            self._preVerb = False
            for i in range(0, action['mainAction_count']):
                entity.DoVerb(self, action['mainAction'], 1)
                
    def EatStuff(self):
        if self._canEat:
            qty = (self.LocalPlayer.EnergyMax - self.LocalPlayer.Energy) / 10
            item = self.LocalPlayer.Inventory.GetItemsByClassId('meat')[0]
            if item == None:
                print("Out of food!")
                self.Done()
                return
            if item.Count < qty:
                qty = item.Count
            print('Eating', str(qty), 'meat.')
            item.DoVerb(self, 'eat', qty)
            self._canEat = False
            
    def HandlePlayerFound(self):
        print("Player found!")
        self._timer = threading.Timer(2, self.Done)
        return False
                
    def Done(self):
        print("Got Loot:")
        for k, v in self._loot.iteritems():
            print("\t ", k, ': ', v)
        self.Logout()
        self.StopSelf()
        
actions = [
           {'entity_id': 'npc_piggy', 'preAction': 'pet', 'preAction_count': 2, 'mainAction': 'nibble', 'mainAction_count': 2},
           {'entity_id': 'npc_butterfly', 'preAction': None, 'preAction_count': 0, 'mainAction': 'milk', 'mainAction_count': 2},
           {'entity_id': 'npc_chicken', 'preAction': None, 'preAction_count': 0, 'mainAction': 'squeeze', 'mainAction_count': 5}
           ]
        
        
client = AnimalHarvestClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ['Aranna'], actions)

client.StartLogin()
client.WaitForCompletion()