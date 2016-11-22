from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory, ProxyConnectionFactory, SocksProxySocketConnection
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.WorldEvents

class DropClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, items, log = None):
        super(DropClient, self).__init__(connectionFactory, pcId, log)
        self._items = items
        
    def _EventCallback(self, event):
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            inventory = self.LocalPlayer.Inventory
            if self._items == 'all':
                for item in inventory:
                    item.DoVerb(self, 'drop', item.Count)
            else:
                for item in inventory:
                    for itemToDrop in self._items:
                        if item.ClassId == itemToDrop:
                            item.DoVerb(self, 'drop', item.Count)
                            print("Dropping " + str(item.Count) + " " + str(item.Label))
                            break
        if isinstance(event, Glitch.Events.Item.VerbActionEvent):
            print(str(event.Success) + " " + event.Verb)
            

#client = DropClient(ProxyConnectionFactory(SocksProxySocketConnection, PacketDispatcher, '127.0.0.1', 9050), 'PUV6L46JN9L2KS0', ['meat'])
        
client = DropClient(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0', ["meat"])
client.StartLogin()
client.WaitForCompletion()