from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.Item
import Glitch.Events.WorldEvents

class FastTravelClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, destination):
        super(FastTravelClient, self).__init__(connectionFactory, pcId)
        
        self._targetPath = None
        self._destination = destination
        
    def _EventCallback(self, event):
        if type(event).__name__ != "PacketEvent":
            print type(event).__name__
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            destination = self.ActiveLocation.MapData.GetLocationIdByName(self._destination)
            if not destination:
                print("Couldn't find destination!")
                self.Logout()
                self.StopSelf()
            else:
                self.ActiveLocation.GetPathToLocation(self, destination)
        elif isinstance(event, Glitch.Events.WorldEvents.GetPathToLocationEvent):
            if not event.Success:
                print("Failed to find path!")
                self.Logout()
                self.StopSelf()
                return
            self._targetPath = event.Path
            self._targetPath.reverse()
            self._targetPath.pop()
            print("Found a " + str(len(event.Path)) + " step path to destination!")
            self.MoveToNext()
        elif isinstance(event, Glitch.Events.WorldEvents.MoveEndEvent):
            print("Moved to " + self.ActiveLocation.Name + " from " + event.FromLocation.Name + ".")
            if self._targetPath != None:
                if len(self._targetPath) == 0:
                    print("Destination reached!")
                    self.Logout()
                    self.StopSelf()
                else:
                    self.MoveToNext()
            
    def MoveToNext(self):
        location = self._targetPath.pop()
        signpost = self.ActiveLocation.GetSignpostContainingLocationId(location)
        if not signpost:
            print("Couldn't find a connecting signpost!")
            self.Logout()
            self.StopSelf()
            return
        signpost.MoveTo(self, signpost.GetTargetIndexById(location))
        
destination = raw_input("To where may I take you today? ")
clientId = raw_input("And your ID is? ")
proxy = raw_input("Would you care to use a proxy for your trip today (Y/N)? ")

if proxy == 'Y' or proxy == 'y':
    client = FastTravelClient(ProxyConnectionFactory(SocksProxySocketConnection, PacketDispatcher, '127.0.0.1', 9050), clientId, destination)
else:
    client = FastTravelClient(ConnectionFactory(SocketConnection, PacketDispatcher), clientId, destination)
client.StartLogin()
client.WaitForCompletion()