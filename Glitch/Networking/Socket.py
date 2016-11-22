import socket
import threading
import select
import Queue
import struct

class SocketConnection(object):
    def __init__(self, packetDispatcher):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._stopEvent = threading.Event()
        self._packetDispatcher = packetDispatcher
        self._sendQueue = Queue.Queue(100)
        self._sendThread = None
        self._recvThread = None
        
    def Connect(self, address, port = 1443):
        self._socket.connect((address, port))
        print("Connected!")
        
    def Wait(self, timeout = None):
        if self._sendThread:
            self._sendThread.join(timeout)
        if self._recvThread:
            self._recvThread.join(timeout)
        
    def Start(self, readyCallback, callbackArgs = ()):
        self._recvThread = threading.Thread(target = self._RecvHandler)
        self._sendThread = threading.Thread(target = self._SendHandler)
        self._sendThread.start()
        self._recvThread.start()
        readyCallback(*callbackArgs)
        
    def Shutdown(self, readOnly = False):
        if readOnly:
            self._socket.shutdown(socket.SHUT_RD)
        else:
            self._socket.shutdown(socket.SHUT_RDWR)
        
    def Stop(self):
        self._sendQueue.put(None)
        self._stopEvent.set()
        self._sendThread.join()
        self._recvThread.join()
        self._socket.close()
            
    def Send(self, data):
        self._sendQueue.put(data)
            
    @property
    def Dispatcher(self):
        return self._packetDispatcher
            
    def _GotData(self, data):
        self._packetDispatcher.QueueData(data)
        
    def _SendHandler(self):
        while True:
            sendData = self._sendQueue.get()
            if sendData == None:
                print("Send handler shutdown!")
                self._sendQueue.task_done()
                return
            self._socket.sendall(sendData)
            self._sendQueue.task_done()
        
    def _RecvHandler(self):
        while self._stopEvent.isSet() == False:
            value = select.select([self._socket], [], [self._socket], 100)
            if len(value[0]) != 0:
                data = self._socket.recv(1024 * 16)
                if len(data) == 0:
                    print("0-byte recv!")
                    if self._stopEvent.isSet() == False:
                        self.Shutdown()
                        self._sendQueue.put(None)
                        self._stopEvent.set()
                    break
                else:
                    self._GotData(data)
            elif len(value[2]) != 0:
                print("Something went wrong!")
        print("Recv handler shutdown!")
            
class SocksProxySocketConnection(SocketConnection):
    def __init__(self, packetDispatcher, proxyAddress, proxyPort):
        super(SocksProxySocketConnection, self).__init__(packetDispatcher)
        self._proxyAddress = proxyAddress
        self._proxyPort = proxyPort
        self._proxyInitialized = False
        
    def Connect(self, address, port = 1443):
        self._socket.connect((self._proxyAddress, self._proxyPort))
        data = struct.pack(">BBHIB" + str(len(address)) + "sB", 4, 1, port, 1, 0, str(address), 0)
        self._socket.sendall(data)
        
    def Start(self, readyCallback, callbackArgs = ()):
        self._recvThread = threading.Thread(target = self._RecvHandler)
        self._sendThread = threading.Thread(target = self._SendHandler)
        self._sendThread.start()
        self._recvThread.start()
        self._callback = readyCallback
        self._callbackArgs = callbackArgs
        
    def _RecvHandler(self):
        if self._proxyInitialized == False:
            data = self._socket.recv(1024 * 16)
            if len(data) < 8:
                print("Too little data!")
                return
            if ord(data[1]) == 0x5a:
                print("Connected thru proxy!")
                self._proxyInitialized = True
                self._callback(*self._callbackArgs)
            else:
                print("Failed to connect to proxy! Response = " + hex(ord(data[1])))
                return
        super(SocksProxySocketConnection, self)._RecvHandler()
        
class ConnectionFactory(object):
    def __init__(self, connectionClass, dispatcherClass):
        self._connectionClass = connectionClass
        self._dispatcherClass = dispatcherClass
    
    def CreateDispatcher(self):
        return self._dispatcherClass()
    
    def CreateConnection(self):
        return self._connectionClass(self.CreateDispatcher())

class ProxyConnectionFactory(ConnectionFactory):
    def __init__(self, connectionClass, dispatcherClass, proxyAddress, proxyPort):
        super(ProxyConnectionFactory, self).__init__(connectionClass, dispatcherClass)
        self._proxyAddress = proxyAddress
        self._proxyPort = proxyPort
        
    def CreateConnection(self):
        return self._connectionClass(self.CreateDispatcher(), self._proxyAddress, self._proxyPort)
                
    