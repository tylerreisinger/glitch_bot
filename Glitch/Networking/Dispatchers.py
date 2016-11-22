import Queue
import threading
import struct

class _PacketDispatcherWorkerThread(threading.Thread):
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        threading.Thread.__init__(self)
        
    def run(self):
        while self._dispatcher._stopEvent.isSet() == False:
            data = self._dispatcher._dataQueue.get()
            with self._dispatcher._dataLock:
                if self._dispatcher._isPacketInProgress:
                    if len(data) + len(self._dispatcher._packetBuffer) > self._dispatcher._targetLength:
                        neededLength = self._dispatcher._targetLength - len(self._dispatcher._packetBuffer)
                        self._dispatcher._packetBuffer += data[:neededLength]
                        print("We got a packet (continued, multiple in buffer)! Length = " + str(len(self._dispatcher._packetBuffer)))
                        self._dispatcher._target._FullPacketReceived(self._dispatcher._packetBuffer)
                        data = data[neededLength:]
                    else:
                        self._dispatcher._packetBuffer += data
                        print("Got data, amount = " + str(len(self._dispatcher._packetBuffer)) + ". Target = " + str(self._dispatcher._targetLength))
                        if self._dispatcher._targetLength == len(self._dispatcher._packetBuffer):
                            print("We got a packet!")
                            self._dispatcher._target._FullPacketReceived(self._dispatcher._packetBuffer)
                            self._dispatcher._isPacketInProgress = False
                            self._dispatcher._packetBuffer = ''
                            self._dispatcher._targetLength = 0
                            continue
                        else:
                            continue
            while True:
                dataLength = struct.unpack('>I', data[:4])[0]
                if len(data) - 4 == dataLength:
                    print("We got a packet! Length = " + str(dataLength))
                    self._dispatcher._target._FullPacketReceived(data[4:])
                    break
                elif len(data) - 4 > dataLength:
                    print("We got a packet (multiple in buffer)! Length = " + str(dataLength))
                    self._dispatcher._target._FullPacketReceived(data[4:dataLength+4])
                    data = data[dataLength + 4:]
                else:
                    with self._dispatcher._dataLock:
                        print("Got data, amount = " + str(len(data) - 4) + ". Target = " + str(dataLength))
                        self._dispatcher._isPacketInProgress = True
                        self._dispatcher._packetBuffer = data[4:]
                        self._dispatcher._targetLength = dataLength
                    break

class PacketDispatcher(object):
    def __init__(self):
        self._dataQueue = Queue.Queue()
        self._packetBuffer = ''
        self._isPacketInProgress = False
        self._targetLength = 0
        self._handlerThread = None
        self._target = None
        
        self._hasStub = False
    
    def QueueData(self, data):
        self._dataQueue.put(data)
        
    def Start(self, target):
        self._target = target
        self._handlerThread = threading.Thread(target=self._HandlerProc)
        self._handlerThread.start()
        #self._workers.append(_PacketDispatcherWorkerThread(self))
        #self._workers[0].start()
        
    def Wait(self, timeout = None):
        return self._handlerThread.join(timeout)
    
    def Stop(self):
        self._dataQueue.put(None)
        
    def _HandlerProc(self):
        while True:
            data = self._dataQueue.get()
            #print("Got " + str(len(data)) + " bytes of data.")
            if data == None:
                #print("Packet Dispatcher shutting down!")
                return
            if self._hasStub:
                self._packetBuffer += data
                if len(self._packetBuffer) > 4:
                    self._hasStub = False
                    data = self._packetBuffer
                    self._packetBuffer = ''
            if self._isPacketInProgress:
                if len(data) + len(self._packetBuffer) > self._targetLength:
                    neededLength = self._targetLength - len(self._packetBuffer)
                    self._packetBuffer += data[:neededLength]
                    #print("We got a packet (continued, multiple in buffer)! Length = " + str(len(self._packetBuffer)))
                    self._target._FullPacketReceived(self._packetBuffer)
                    data = data[neededLength:]
                    self._isPacketInProgress = False
                    self._packetBuffer = ''
                    self._targetLength = 0
                else:
                    self._packetBuffer += data
                    #print("Got data, amount = " + str(len(self._packetBuffer)) + ". Target = " + str(self._targetLength))
                    if self._targetLength == len(self._packetBuffer):
                        #print("We got a packet!")
                        self._target._FullPacketReceived(self._packetBuffer)
                        self._isPacketInProgress = False
                        self._packetBuffer = ''
                        self._targetLength = 0
                        continue
                    else:
                        continue
            while True:
                if len(data) < 4:
                    self._packetBuffer = data
                    self._hasStub = True
                    break
                dataLength = struct.unpack('>I', data[:4])[0]
                if len(data) - 4 == dataLength:
                    #print("We got a packet! Length = " + str(dataLength))
                    self._target._FullPacketReceived(data[4:])
                    break
                elif len(data) - 4 > dataLength:
                    #print("We got a packet (multiple in buffer)! Length = " + str(dataLength))
                    self._target._FullPacketReceived(data[4:dataLength+4])
                    data = data[dataLength + 4:]
                else:
                    #print("Got data, amount = " + str(len(data) - 4) + ". Target = " + str(dataLength))
                    self._isPacketInProgress = True
                    self._packetBuffer = data[4:]
                    self._targetLength = dataLength
                    break
    
        