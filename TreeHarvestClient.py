from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.WorldEvents

import threading

class TreeHarvestClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, regions, log = None):
        super(TreeHarvestClient, self).__init__(connectionFactory, pcId, log)
        
        self._streetsToVisit = []
        self._regions = regions
        self._path = []
        
        self._doneTrees = {}
        self._activeTree = None
        self._harvestCount = 0
        
        self._loot = {}
        
        self._harvestTimer = None
        
    def _EventCallback(self, event):
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            for region in self._regions:
                regionObject = self.ActiveLocation.MapData.GetRegionByName(region)
                if regionObject:
                    self._streetsToVisit.extend(regionObject.Streets)
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
            for location in self._streetsToVisit:
                if location.Id == self.ActiveLocation.Id:
                    self._streetsToVisit.remove(location)
                    print("Found " + str(len(self.ActiveLocation.Trees)) + " trees.")
                    self.HarvestOne()
                    return
            self.MoveToNext()
            
        elif isinstance(event, Glitch.Events.Item.VerbActionEvent):
            if event.Verb == 'harvest' or event.Verb == 'pet' or event.Verb == 'water':
                print("Done! " + str(event.Success))
                if event.Success:
                    self._harvestTimer = threading.Timer(2.050, self.DoNextThread)
                    self._harvestTimer.start()
                else:
                    self.HarvestOne()
            elif event.Verb == 'eat':
                self.HarvestOne()
                
        elif isinstance(event, Glitch.Events.Item.ItemAddedEvent):
            if event.Item.ClassId not in self._loot:
                self._loot[event.Item.ClassId] = event.Item.Count
            else:
                self._loot[event.Item.ClassId] += event.Item.Count
                
        elif isinstance(event, Glitch.Events.Item.ItemDeletedEvent):
            if event.Item.ClassId not in self._loot:
                self._loot[event.Item.ClassId] = -event.Item.Count
            else:
                self._loot[event.Item.ClassId] -= event.Item.Count
                
        elif isinstance(event, Glitch.Events.Item.ItemCountChangedEvent):
            deltaCount = event.Item.Count - event.OldItemCount
            if event.Item.ClassId not in self._loot:
                self._loot[event.Item.ClassId] = deltaCount
            else:
                self._loot[event.Item.ClassId] += deltaCount
            
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
                print("Finished!")
                print("Got Loot: ")
                for k, v in self._loot.iteritems():
                    print("\t" + k + " = " + str(v))
                self.Logout()
                self.StopSelf()
                
    def HarvestOne(self):
        if self.LocalPlayer.Energy < self.LocalPlayer.EnergyMax / 2:
            self.EatStuff()
            return
        
        if self._harvestCount == 2:
            self._activeTree = None
            self._harvestCount = 0
        
        trees = self.ActiveLocation.Trees
        treeToUse = None
        if self._activeTree:
            treeToUse = self._activeTree
        else:
            count = 0
            for tree in trees:
                count += 1
                if tree not in self._doneTrees:
                    treeToUse = tree
                    self._activeTree = tree
                    self._doneTrees[tree] = True
                    print("Tree " + str(count) + "/" + str(len(trees)))
                    break
            if treeToUse == None:
                self.MoveToNext()
                return

        #if treeToUse.FruitQuantity > 0:
        self.LocalPlayer.MoveTo(self, treeToUse.XPosition, treeToUse.YPosition)
        treeToUse.DoVerb(self, 'harvest', 1)
        print("Harvesting...")
        self._harvestCount += 1
        #else:
        #    if 1==2 and 'water' in treeToUse.VerbStates and treeToUse.VerbStates['water'].Disabled == False:
        #        treeToUse.DoVerb(self, 'water', 1)
        #        print("Watering...")
        #    elif 1==2 and 'pet' in treeToUse.VerbStates and treeToUse.VerbStates['pet'].Disabled == False:
        #        treeToUse.DoVerb(self, 'pet', 1)
        #        print("Petting...")
        #    else:
        #        self._activeTree = None
        #        self._harvestCount = 0
        #        self.HarvestOne()
                
    def EatStuff(self):
        meat = self.LocalPlayer.Inventory.GetItemsByClassId('meat')
        qty = (self.LocalPlayer.EnergyMax - self.LocalPlayer.Energy) / 10
        if len(meat) == 0:
            return
        i = meat[0]
        amount = i.Count
        if qty < amount:
            amount = qty
        i.DoVerb(self, 'eat', amount)
        qty -= amount
            
    def DoNextThread(self):
        self.HarvestOne()
            
client = TreeHarvestClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ['Groddle Meadow'])
client.StartLogin()
client.WaitForCompletion()