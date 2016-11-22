from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, ConnectionFactory
from Glitch.Client.GlitchClient import GlitchClientBase

import Glitch.Events.Event
import Glitch.Events.WorldEvents

class CraftingClient(GlitchClientBase):
    def __init__(self, connectionFactory, pcId, regions, recipe, tool, log = None):
        super(CraftingClient, self).__init__(connectionFactory, pcId, log)
        
        self._recipe = recipe
        self._tool = tool
        
    def _EventCallback(self, event):
        if isinstance(event, Glitch.Events.Event.LoginCompleteEvent):
            pass
        
        