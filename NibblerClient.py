from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.WorldEvents

import threading

class AnimalAction(object):
    def __init__(self, animal, actions, times):
        self._animal = animal
        self._actions = actions
        self._times = times
        
    def DoAction(self, client):
        for action in self._actions:
            for i in range(0, self._times):
                self._animal.DoVerb(client, action, 1)

class NibblerClient(GlitchClientBase):
    
    def __init__(self, connectionFactory, pcId, regions, log = None):
        super(NibblerClient, self).__init__(connectionFactory, pcId, log)
        
        self._streetsToVisit = []
        self._regions = regions
        self._path = []
        self._deltaMeat = 0
        self._meatCountInitial = 0
        self._verbCount = 0
        
        self._pigsDepleted = {}
        self._currentPig = None
        self._timer = None
        
        
    def _EventCallback(self, event):
        if isinstance(event, Glitch.Events.Event.PacketEvent):
            if event.Type == 'itemstack_verb':
                self._log.PacketReceived(event.packetObject)
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
                
        if isinstance(event, Glitch.Events.WorldEvents.GetPathToLocationEvent):
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
            
        if isinstance(event, Glitch.Events.WorldEvents.MoveEndEvent):
            print("Moved to " + self.ActiveLocation.Name + " from " + event.FromLocation.Name)
            for location in self._streetsToVisit:
                if location.Id == self.ActiveLocation.Id:
                    self._streetsToVisit.remove(location)
                    print("Found " + str(len(self.ActiveLocation.GetEntitesByClassId('npc_piggy'))) + " pigs.")
                    self.NibbleOne()
                    return
            self.MoveToNext()
                    
        if isinstance(event, Glitch.Events.Item.VerbActionEvent):
            if event.Verb == 'nibble':
                print("Success = " + str(event.Success))
                self._verbCount += 1
                if self._verbCount == 2:
                    self._verbCount = 0
                    self.NibbleOne()
            elif event.Verb == 'pet':
                print("Petting success = " + str(event.Success))
            
    def MoveToNext(self):
        if len(self._path) > 0:
            location = self._path.pop()
            signpost = self.ActiveLocation.GetSignpostContainingLocationId(location)
            if signpost == None:
                print("No connecting signpost!")
                self.MoveToNext()
                #self.Logout()
                #self.StopSelf()
                return
            signpost.MoveTo(self, signpost.GetTargetIndexById(location))
        else:
            if len(self._streetsToVisit) > 0:
                self.ActiveLocation.GetPathToLocation(self, self._streetsToVisit[len(self._streetsToVisit) - 1].Id)
            else:
                print("Got a total of " + str(self.LocalPlayer.Inventory.CountAllByClassId('meat') - self._meatCountInitial) + " meat.")
                self.Logout()
                self.StopSelf()
                
    def NibbleOne(self):
        pigs = self.ActiveLocation.GetEntitesByClassId('npc_piggy')
        count = 0
        for pig in pigs:
            count += 1
            if self.LocalPlayer.Energy < self.LocalPlayer.EnergyMax / 2:
                self.EatStuff()
            if pig.Id not in self._pigsDepleted:
                self.LocalPlayer.MoveTo(self, pig.XPosition, pig.YPosition)
                print("Pig " + str(count) + "/" + str(len(pigs)) + " (" + pig.Label + ") X: " + str(pig.XPosition) + " Y: " + str(pig.YPosition))
                self._currentPig = pig
                self._timer = threading.Timer(.4, self.DoPet, (pig,))
                self._timer.start()
                self._pigsDepleted[pig.Id] = True
                return
        print(str(count) + "----")
        self._pigsDepleted = {}
        self.MoveToNext()
                
    def EatStuff(self):
        qty = (self.LocalPlayer.EnergyMax - self.LocalPlayer.Energy) / 10
        print("Eating " + str(qty) + " meat.")
        items = self.LocalPlayer.Inventory.GetItemsByClassId('meat')
        for item in items:
            if qty <= 0:
                break
            eatCount = item.Count
            if qty < item.Count:
                eatCount = qty
            item.DoVerb(self, 'eat', eatCount)
            qty - eatCount
            
    def DoNibble(self, pig):
        pig.DoVerb(self, 'nibble', 1)
        pig.DoVerb(self, 'nibble', 1)
        
    def DoPet(self, pig):
        pig.DoVerb(self, 'pet', 1)
        pig.DoVerb(self, 'pet', 1)
        self._timer = threading.Timer(.25, self.DoNibble, (pig,))
        self._timer.start()
#client = NibblerClient(ProxyConnectionFactory(SocksProxySocketConnection, PacketDispatcher, '127.0.0.1', 9050), 'PUV6L46JN9L2KS0', ['Groddle Meadow'])
 
#client = NibblerClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ['Groddle Meadow', 'Groddle Forest', 'Groddle Heights', 'Alakol', 'Bortola'])       
client = NibblerClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ['Tamila', 'Rasana', 'Andra', 'Aranna', 'Besara'])

client.StartLogin()
client.WaitForCompletion()