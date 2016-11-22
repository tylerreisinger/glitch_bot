from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.WorldEvents

import threading

class MiningFilter(object):
    def __init__(self):
        pass
    
    def CanMineMetal(self, client, currentLoot):
        return True
    
    def CanMineSparkly(self, client, currentLoot):
        return True
    
    def CanMineBeryl(self, client, currentLoot):
        return False
    
    def CanMineDullite(self, client, currentLoot):
        return True

class MiningClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, path, rockFilter, log = None):
        super(MiningClient, self).__init__(connectionFactory, pcId, log)
        
        self._path = path
        
        self._filter = rockFilter
        
        self._pathToLocation = []
        
        self._loot = {}
        
        self._targetLocation = None
        
        self._activeRock = None
        self._timerThread = None
        
        self._isUnloading = False
        
    def _EventCallback(self, event):
        if self._isUnloading:
            self.UnloadingEventCallback(event)
            return
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            
            for i in range(0, len(self._path)):
                self._path[i] = self.ActiveLocation.MapData.GetLocationIdByName(self._path[i])
            
            if self.ActiveLocation.Id != self._path[0]:
                self.MoveToNext()
            else:
                self.MineSomething()
        
        elif isinstance(event, Glitch.Events.WorldEvents.GetPathToLocationEvent):
            if event.Success == True:
                self._pathToLocation = event.Path
                self._pathToLocation.reverse()
                self._pathToLocation.pop()
                self.TraversePath()
            else:
                print("Get path failed!")
                self.Quit()
                
        elif isinstance(event, Glitch.Events.WorldEvents.MoveEndEvent):
            if event.Success == True:
                print("Moved to " + self.ActiveLocation.Name + " from " + event.FromLocation.Name)
                if len(self._pathToLocation) > 0:
                    self.TraversePath()
                else:
                    self.MineSomething()
                
        elif isinstance(event, Glitch.Events.Item.VerbActionEvent):
            if event.Success == True:
                if event.Verb == 'drink' or event.Verb == 'eat':
                    self.MineSomething()
                elif event.Verb == 'mine':
                    self._timerThread = threading.Timer(4.5, self._MineThreadCallback)
                    self._timerThread.start()
                elif event.Verb == 'repair':
                    self._timerThread = threading.Timer(10.0, self._MineThreadCallback)
                    self._timerThread.start()
            else:
                print("Failure!")
                self.MineSomething()
                
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
                
    def UnloadingEventCallback(self, event):
        if isinstance(event, Glitch.Events.WorldEvents.MoveEndEvent):
            if self.ActiveLocation.Name.find('House') == -1:
                self.ActiveLocation.Doors[0].Enter(self)
            else:
                self.DepositNext()
        if isinstance(event, Glitch.Events.Item.VerbActionEvent):
            if event.Success:
                if event.Verb == 'deposit' or event.Verb == 'drop':
                    self.DepositNext()
            else:
                print("Depositing Failure!")
            
    def DepositNext(self):
        
        itemsToDrop = ['gem_diamond', 'gem_ruby', 'gem_moonstone', 'gem_amber', 'gem_sapphire']
        
        for item in itemsToDrop:
            stacks = self.LocalPlayer.Inventory.GetItemsByClassId(item)
            if len(stacks) > 0:
                stacks[0].DoVerb(self, 'drop', stacks[0].Count)
                print("Dropping " + str(stacks[0].Count) + " " + item)
                return
        
        itemsToDeposit = ['sparkly', 'metal_rock', 'beryl', 'dullite']
        for item in itemsToDeposit:
            itemCount = self.LocalPlayer.Inventory.CountAllByClassId(item)
            if itemCount > 0:
                storageDepositBoxes = self.ActiveLocation.GetEntitiesByClassId('bag_furniture_sdb')
                for sdb in storageDepositBoxes:
                    if sdb.StorageItem == item:
                        self.LocalPlayer.MoveTo(self, sdb.XPosition, sdb.YPosition)
                        sdb.DoVerb(client, 'deposit', 1, {'target_item_class': item, 'check_for_proximity': False, 'target_item_class_count': itemCount})
                        print("Deposited " + str(itemCount) + " units of " + item)
                        return
        
        
        print("Done unloading")
        #self.Logout()
        #self.StopSelf()          
        self._isUnloading = False
        self.LocalPlayer.LeaveHome(self)
        
    def MoveToNext(self):
        count = 0
        nextLocation = None
        for location in self._path:
            if location == self.ActiveLocation.Id:
                if len(self._path) > count + 1:
                    nextLocation = self._path[count + 1]
                else: 
                    nextLocation = self._path[0]
            count += 1
        if nextLocation == None:
            nextLocation = self._path[0]
        
        self._targetLocation = nextLocation
        self.ActiveLocation.GetPathToLocation(self, self._targetLocation)
        
    def TraversePath(self):
        if len(self._pathToLocation) > 0:
            location = self._pathToLocation.pop()
            signpost = self.ActiveLocation.GetSignpostContainingLocationId(location)
            if signpost == None:
                print("No connecting signpost!")
                self.Quit()
                return
            signpost.MoveTo(self, signpost.GetTargetIndexById(location))
            
    def MineSomething(self):
        if self.LocalPlayer.Inventory.GetFreeSlotsInContainersByClassId('bag_bigger_blue', 'bag_bigger_black', 'bag_bigger_green', 'bag_bigger_pink', 'bag_bigger', 
                                                                        'bag_generic_blue', 'bag_generic_black', 'bag_generic_green', 'bag_generic_pink', 'bag_generic') == 0:
            print("Inventory is full")
            self._isUnloading = True
            self._activeRock = None
            self.LocalPlayer.GoHome(self)
            return
            
        if self.LocalPlayer.Inventory.GetItemsByClassId('tinkertool')[0].Durability < 100:
            self.LocalPlayer.Inventory.GetItemsByClassId('tinkertool')[0].DoVerb(self, 'repair', 1)
            print("Repairing tinkertool...")
            return
        if self.LocalPlayer.Inventory.GetItemsByClassId('fancy_pick')[0].IsBroken == True:
            self.LocalPlayer.Inventory.GetItemsByClassId('fancy_pick')[0].DoVerb(self, 'repair', 1)
            print("Repairing pick...")
            return
        if self.LocalPlayer.GetBuffByName('Impervious Miner') == None:
            drinks = self.LocalPlayer.Inventory.GetItemsByLabel('Earthshaker')
            if len(drinks) > 0:
                drinks[0].DoVerb(self, 'drink', 1)
                print("Drinking earthshaker.")
            else:
                print("Out of earthshakers!")
                self.Quit()
            return
        
        if self.LocalPlayer.Energy < self.LocalPlayer.EnergyMax / 2:
            food = self.LocalPlayer.Inventory.GetItemsByLabel('Lemburger')
            if len(food) > 0:
                food[0].DoVerb(self, 'eat', 1)
                print("Eating food.")
            else:
                print("Out of food!")
                self.Quit()
            return
        
        rock = None
        
        if self._activeRock != None and self.ActiveLocation.GetEntityById(self._activeRock.Id) != None and self._activeRock.S != 'visible:false':
            rock = self._activeRock
        else:
            rockClassList = []
            if self._filter.CanMineMetal(self, self._loot):
                rockClassList.extend(['rock_metal_1', 'rock_metal_2', 'rock_metal_3'])
            if self._filter.CanMineBeryl(self, self._loot):
                rockClassList.extend(['rock_beryl_1', 'rock_beryl_2', 'rock_beryl_3'])
            if self._filter.CanMineSparkly(self, self._loot):
                rockClassList.extend(['rock_sparkly_1', 'rock_sparkly_2', 'rock_sparkly_3'])
            if self._filter.CanMineDullite(self, self._loot):
                rockClassList.extend(['rock_dullite_1', 'rock_dullite_2', 'rock_dullite_3'])
                
            allRocks = self.ActiveLocation.GetEntitiesByClassId(*rockClassList)
            rocks = []
            for rock in allRocks:
                if rock.S != 'visible:false':
                    rocks.append(rock)
        
            if len(rocks) > 0:
                rock = rocks[0]
                self._activeRock = rock
            else:
                print("Mined all rocks in area!")
                self.MoveToNext()
                return
        
        print("Mining " + rock.ClassId)
        self.LocalPlayer.MoveTo(self, rock.XPosition, rock.YPosition)
        rock.DoVerb(self, 'mine', 1, {'check_for_proximity': False})
        
    def Quit(self):
        print("Got Loot: ")
        for k, v in self._loot.iteritems():
            print("\t" + k + ": " + v)
        self.Logout()
        self.StopSelf()
    def _MineThreadCallback(self):
        self.MineSomething()
        
    def _DoMineCallback(self, rock):
        rock.DoVerb(self, 'mine', 1, {'check_for_proximity': False})
            
    
client = MiningClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ['Kikal Kalzo', 'Tibsii Wibbs', 'Hamli Egza', 'Kotteletti Kota', 'Dhalakk Dalliance', 'Quluuwaa Luwa', 'Selsi Loss'], MiningFilter())
client.StartLogin()
client.WaitForCompletion()
        