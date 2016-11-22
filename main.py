from Glitch.Networking.Dispatchers import PacketDispatcher
from Glitch.Networking.Socket import SocketConnection, SocksProxySocketConnection, ConnectionFactory, ProxyConnectionFactory
from Glitch.Client.GlitchClient import GlitchClientBase

client = GlitchClientBase(ConnectionFactory(SocketConnection, PacketDispatcher), 'PA9T2PFOUTD23B0')
client.StartLogin()
client.WaitForCompletion()