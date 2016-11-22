import httplib
import time
import xml.dom.minidom as xmlparser
import threading
import Queue
from amfast.decoder import Decoder
from amfast.encoder import Encoder

import json

from Glitch.Events.Event import PacketEvent, LoginCompleteEvent, ShutdownEvent, ReloginStartEvent, ReloginEndEvent
from Glitch.Events.Crafting import CraftingStartEvent, CraftingBeginEvent, CraftingEndEvent, RecipeRequestEvent
from Glitch.Events.Item import VerbQueryEvent, VerbActionEvent, ItemAddedEvent, ItemDeletedEvent, ItemCountChangedEvent, TeleportationScriptReadEvent, NoteReadEvent
from Glitch.Events.Messaging import RoomMessageEvent, LocalMessageEvent
from Glitch.Events.WorldEvents import MoveEndEvent, MoveStartEvent
from Glitch.Client.Player import LocalPlayer
from Glitch.Client.Inventory import CreateItem
from Glitch.Client.Messaging import ChatManager
from Glitch.Client.World import ActiveLocation

import Glitch.Events.Item

class LoginHelper(object):
    def __init__(self, pcId):
        self._pcId = pcId
        
    def GetLoginInfo(self):
        connection = httplib.HTTPConnection('www.glitch.com')
        connection.request('GET', '/local.php?p=' + self._pcId + '&cb=' + str(int(time.time() * 1000)))
        response = connection.getresponse()
        
        if response.status == 200:
            body = response.read()
            print(body)
            bodyDOM = xmlparser.parseString(body)
            token = bodyDOM.getElementsByTagName('token')[0].firstChild.nodeValue
            host = bodyDOM.getElementsByTagName('host')[0].firstChild.nodeValue
            return (token, host)
        else:
            print("Request for login token failed with code " + str(response.status))
            return None

class PacketLog(object):
    def __init__(self, fileName):
        self._logFile = open(fileName, 'w')
        
    def PacketReceived(self, packet):
        self._logFile.write("Recevied\n" + json.dumps(packet, indent = 3))
        self._logFile.flush()
        
    def PacketSent(self, packet):
        self._logFile.write("Sent\n" + json.dumps(packet, indent = 3))
        self._logFile.flush()
            
class GlitchClientBase(object):

    def __init__(self, connectionFactory, pcId, log = None):
        self._token = None
        self._connectionFactory = connectionFactory
        self._connection = connectionFactory.CreateConnection()
        self._messageId = 1
        self._serverAddress = None
        self._eventQueue = Queue.Queue()
        self._eventThread = threading.Thread(target = self._EventThreadFunc)
        self._pcId = pcId
        self._eventUserData = {}
        self._packetHandlers = {}
        self._log = PacketLog('/home/tyler/GlitchPacketLogs/ClientLog')
        
        self._shutdownEvent = threading.Event()
        
        self._pingTimer = threading.Timer(10.0, self._DoPing)
        
        self._localPlayer = None
        self._activeLocation = None
        self._chatManager = None
        
        self._reloginPreviousLocation = None
        self._shutdownSelfThread = None
        
        self._reloginInformation = None
    
    def StartLogin(self):
        login = LoginHelper(self._pcId)
        loginInfo = login.GetLoginInfo()
        self._token = loginInfo[0]
        self._serverAddress = loginInfo[1][:loginInfo[1].rfind(':')]
        
        if loginInfo != None:
            print("Login token = " + loginInfo[0])
        else:
            print("Login Failed!")
            return
        
        self._connection.Connect(self._serverAddress)
        self._connection.Start(self._ConnectionReadyInitial)
        
    def SendPacket(self, typeName, parameters, msgId = True, userData = None, callbackFn = None, callbackArgs = []):
        packetObj = {'type' : typeName}
        returnId = None
        if msgId == True:
            returnId = self._messageId
            packetObj['msg_id'] = self._messageId
            self._messageId += 1
            userDataObj = {}
            hasUserData = False
            if userData:
                userDataObj[u'user_data'] = userData
                hasUserData = True
            if callbackFn:
                userDataObj[u'callback_fn'] = callbackFn
                userDataObj[u'callback_args'] = callbackArgs
                hasUserData = True
            if hasUserData:
                self._eventUserData[returnId] = userDataObj
        packetObj.update(parameters)
        self._OnPacketSend(packetObj)
        encoder = Encoder(amf3 = True)
        packet = encoder.encode(packetObj)
        self._connection.Send(packet)
        return returnId
    
    def WaitForCompletion(self, timeout = None):
        self._shutdownEvent.wait(timeout)
        
    def QueueEvent(self, event):
        self._eventQueue.put(event)
        
    @property
    def LocalPlayer(self):
        return self._localPlayer
    
    @property
    def ActiveLocation(self):
        return self._activeLocation
    
    def Logout(self):
        self.SendPacket('logout', {})
    
    def Shutdown(self):
        self._pingTimer.cancel()
        self._connection.Shutdown(True)
        self._connection.Stop()
        self._connection.Dispatcher.Stop()
        self.QueueEvent(ShutdownEvent())
        self._connection.Wait()
        self._connection.Dispatcher.Wait()
        self._eventThread.join()
        print("Shutdown complete!")
        
    def ShutdownSelf(self, callback = None, callbackArgs = ()):
        self._pingTimer.cancel()
        self._connection.Shutdown(True)
        self._connection.Stop()
        self._connection.Dispatcher.Stop()
        self.QueueEvent(ShutdownEvent())
        self._connection.Wait()
        self._connection.Dispatcher.Wait()
        self._shutdownSelfThread = threading.Thread(target = self._ShutdownSelfThread, args = (callback, callbackArgs))
        self._shutdownSelfThread.start()
        
    def Stop(self):
        self.Shutdown()
        self._activeLocation = None
        self._chatManager = None
        self._localPlayer = None
        self._shutdownEvent.set()
        
    def StopSelf(self):
        self.ShutdownSelf(self._StopSelf)
    
    def _ShutdownSelfThread(self, callback, callbackArgs):
        self._eventThread.join()
        print("Shutdown complete!")
        if callback:
            callback(*callbackArgs)
            
    def _StopSelf(self):
        self._activeLocation = None
        self._chatManager = None
        self._localPlayer = None
        self._shutdownEvent.set()
        
    def _ConnectionReadyInitial(self):
        self._connection.Dispatcher.Start(self)
        
        self._eventThread.start()
        self.SendPacket('login_start', {'token' : self._token})
        
    def _ConnectionReadyRelog(self, token, reloginType, sendMoveEvent):
        self._connection.Dispatcher.Start(self)
        
        self.SendPacket('relogin_start', {'token': token, 'relogin_type': reloginType}, callbackFn = self._ReloginStart, callbackArgs = (token, reloginType, sendMoveEvent))

        
    def _ReloginOnDisconnect(self, serverAddress, token, reloginType, previousLocation = None, sendMoveEvent = False):
        self._reloginInformation = (serverAddress, token, reloginType, previousLocation, sendMoveEvent)
    
    def _StartRelogin(self, serverAddress, token, reloginType, previousLocation = None, sendMoveEvent = False):
        self._reloginPreviousLocation = previousLocation
        self.QueueEvent(ReloginStartEvent())
        self.ShutdownSelf(self._FinishRelogin, (serverAddress, token, reloginType, sendMoveEvent))
       
        
    def _FinishRelogin(self, serverAddress, token, reloginType, sendMoveEvent):
        self._activeLocation = None
        self._eventQueue = Queue.Queue()
        self._eventUserData = {}
        self._connection = self._connectionFactory.CreateConnection()
        self._connection.Connect(serverAddress)
        self._eventThread = threading.Thread(target = self._EventThreadFunc)
        self._eventThread.start()
        self._connection.Start(self._ConnectionReadyRelog, (token, reloginType, sendMoveEvent))
        
    def _ReloginStart(self, packet, token, reloginType, sendMoveEvent):
        if packet.packetObject[u'success'] == False:
            self.StopSelf()
            print("FATAL: Relogin start returned failure! Aborting.")
        else:
            self._activeLocation = ActiveLocation(packet.packetObject[u'location'])
            self._DoPing()
            if sendMoveEvent:
                self.QueueEvent(MoveStartEvent(packet.packetObject, self._reloginPreviousLocation))
            self.SendPacket('relogin_end', {'relogin_type': reloginType}, callbackFn = self._ReloginEnd, callbackArgs = (token, reloginType, sendMoveEvent))
            
    def _ReloginEnd(self, packet, token, reloginType, sendMoveEvent):
        if packet.packetObject[u'success'] == False:
            self.StopSelf()
            print("FATAL: Relogin end returned failure! Aborting.")
        else:
            self._activeLocation._MoveEnd(packet.packetObject[u'location'])
            self.QueueEvent(ReloginEndEvent())
            if sendMoveEvent:
                self.QueueEvent(MoveEndEvent(packet.packetObject, self._reloginPreviousLocation))
    
    def _FullPacketReceived(self, packet):
        decoder = Decoder(amf3 = True)
        packetObj = decoder.decode(packet)
        self._OnPacketReceived(packetObj)
        self._eventQueue.put(PacketEvent(packetObj))
        
    def _OnPacketReceived(self, packet):
        if 1==1 or self._log and packet[u'type'] != 'location_item_moves' and packet[u'type'] != 'login_start' and packet[u'type'] != 'login_end' and packet[u'type'] != 'location_event' and packet[u'type'] != "item_state":
            pass
            #self._log.PacketReceived(packet)
    
    def _OnPacketSend(self, packet):
        if 1==1 or self._log:
            pass
            #self._log.PacketSent(packet)
        
    def _LocationChange(self, packet):
        self._activeLocation = ActiveLocation(packet)
        
    def _EventThreadFunc(self):
        while True:
            try:
                event = self._eventQueue.get()
                if isinstance(event, PacketEvent):
                    if event.Type == 'login_start':
                        if event.packetObject[u'success'] == True:
                            self._localPlayer = LocalPlayer(self._pcId, event.packetObject)
                            self._chatManager = ChatManager(event.packetObject[u'global_chat_group'], event.packetObject[u'live_help_group'])
                            self._DoPing()
                            print("Login Success!")
                            self._activeLocation = ActiveLocation(event.packetObject[u'location'])
                            self.SendPacket('login_end', {})
                    elif event.Type == 'login_end' and event.packetObject[u'success'] == True:
                        self._activeLocation._MoveEnd(event.packetObject[u'location'])
                    elif event.Type == 'pc_move_xy':
                        self._HandleMoveXY(event.packetObject)
                    elif event.Type == 'pc_signpost_move' or event.Type == 'pc_teleport_move' or event.Type == 'pc_follow_move' or event.Type == 'pc_door_move':
                        self.ActiveLocation._HandlePcMove(self, event.packetObject)
                    elif event.Type == 'buff_remove':
                        self.LocalPlayer._RemoveBuff(self, event.packetObject[u'tsid'])
                    elif event.Type == 'buff_start':
                        self.LocalPlayer._AddBuff(self, event.packetObject)
                    elif event.Type == 'buff_update':
                        self.LocalPlayer._UpdateBuff(self, event.packetObject)
                    elif event.Type == 'server_message' and event.packetObject[u'action'] == 'CLOSE' and event.packetObject[u'msg'] == 'CONNECT_TO_ANOTHER_SERVER':
                        if self._reloginInformation:
                            self._StartRelogin(*self._reloginInformation)
                            self._reloginInformation = None
                        else:
                            print('Server closed the connection!')
                            self._StopSelf()
                    if u'changes' in event.packetObject:
                        self._HandleChangeObject(event.packetObject[u'changes'])
                    if u'teleportation' in event.packetObject:
                        self._localPlayer._TeleportUpdate(event.packetObject)
                    newEvent = self._CreateEvents(event)
                    if u'msg_id' in event.packetObject:
                        if event.packetObject[u'msg_id'] in self._eventUserData:
                            userDataObj = self._eventUserData[event.packetObject[u'msg_id']]
                            if 'callback_fn' in userDataObj:
                                userDataObj['callback_fn'](event, *userDataObj[u'callback_args'])
                            del self._eventUserData[event.packetObject[u'msg_id']]
                    if newEvent:
                        self.QueueEvent(newEvent)
                elif isinstance(event, ShutdownEvent):
                    print("Shutting down...")
                    self._EventCallback(event)
                    self._eventQueue.task_done()
                    return
                self._EventCallback(event)
            except Exception:
                self.Logout()
                self.StopSelf()
                raise
            self._eventQueue.task_done()
            
    def _CreateEvents(self, packetEvent):
        event = None
        
        if packetEvent.Type == 'itemstack_verb_menu':
            pass#event = VerbQueryEvent(packetEvent.packetObject[u'itemDef'])
        elif packetEvent.Type == 'itemstack_verb':
            pass#event = VerbActionEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'making_start':
            event = CraftingStartEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'make_known_complete':
            event = CraftingEndEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'login_end' and packetEvent.packetObject[u'success'] == True:
            event = LoginCompleteEvent()
        elif packetEvent.Type == 'pc_groups_chat':
            event = RoomMessageEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'pc_local_chat':
            event = LocalMessageEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'recipe_request':
            event = RecipeRequestEvent(packetEvent.packetObject)
        elif packetEvent.Type == 'teleport_move_start':
            self._HandleMoveStart(packetEvent.packetObject, 'teleport')
        elif packetEvent.Type == 'teleportation_script_view':
            item = None
            if u'itemstack_tsid' in packetEvent.packetObject:
                item = self._localPlayer.Inventory.GetItemById(packetEvent.packetObject[u'itemstack_tsid'])
            event = TeleportationScriptReadEvent(packetEvent.packetObject, item)
        elif packetEvent.Type == 'note_view':
            item = None
            if u'itemstack_tsid' in packetEvent.packetObject:
                item = self._localPlayer.Inventory.GetItemById(packetEvent.packetObject[u'itemstack_tsid'])
            event = NoteReadEvent(packetEvent.packetObject, item)
        if event:
            if u'msg_id' in packetEvent.packetObject:
                event._msgId = packetEvent.packetObject[u'msg_id']
                if packetEvent.packetObject[u'msg_id'] in self._eventUserData:
                    userDataObj = self._eventUserData[packetEvent.packetObject[u'msg_id']]
                    if 'user_data' in userDataObj:
                        event._userData = userDataObj['user_data']
        return event
        
    def _EventCallback(self, event):
        print type(event).__name__
        if isinstance(event, PacketEvent):
            print(event.packetObject[u'type'])
        if isinstance(event, LoginCompleteEvent):
            self.Logout()
            self.StopSelf()
            #self.LocalPlayer.GoHome(self)
            #bags = []
            #for item in self.LocalPlayer.Inventory:
            #    if item.ParentContainer == None:
            #        bags.append(item)
            #        print(item.Label)
            #self.Logout()
            #self.StopSelf()
        
    def _DoPing(self):
        self.SendPacket('ping', {'tsid' : self._pcId}, False)
        self._pingTimer = threading.Timer(10.0, self._DoPing)
        self._pingTimer.start()
        
    def _HandleMoveXY(self, packetObj):
        if u'pc' in packetObj:
            if packetObj[u'pc'][u'tsid'] == self._localPlayer.Id:
                self._localPlayer._MoveXY(packetObj[u'pc'][u'x'], packetObj[u'pc'][u'y'])
            else:
                self._activeLocation._PlayerMoved(packetObj[u'pc'][u'tsid'], packetObj[u'pc'][u'x'], packetObj[u'pc'][u'y'])
                
    def _HandleMoveStart(self, packetObj, reloginType):
        if not u'success' in packetObj or packetObj[u'success'] == True:
            if u'hostport' in packetObj:
                self._ReloginOnDisconnect(packetObj[u'hostport'][:packetObj[u'hostport'].find(':')], packetObj[u'token'], reloginType, self._activeLocation, True)
            else:
                previousLocation = self._activeLocation
                self._LocationChange(packetObj[u'location']) 
                event = MoveStartEvent(packetObj, previousLocation)
                self.QueueEvent(event)
                self.SendPacket(packetObj[u'type'].replace('start', 'end'), {'from_location_tsid': previousLocation.Id, 'to_location_tsid': packetObj[u'loading_info'][u'to_tsid']}, callbackFn = self._HandleMoveEnd, callbackArgs = (previousLocation,))
                event = MoveStartEvent(packetObj, previousLocation)
                self.QueueEvent(event)
        else:
            event = MoveStartEvent(packetObj, self._activeLocation)
            self.QueueEvent(event)
    
    def _HandleMoveEnd(self, packet, previousLocation):
        if packet.packetObject[u'success'] == True:
            self._activeLocation._MoveEnd(packet.packetObject[u'location'])
            event = MoveEndEvent(packet.packetObject, previousLocation)
            self.QueueEvent(event)
        else:
            event = MoveEndEvent(packet.packetObject, previousLocation)
            self.QueueEvent(event)
                
            
    def _HandleChangeObject(self, obj):
        if u'stat_values' in obj:
            self._localPlayer._StatsChange(obj[u'stat_values'])
        if u'itemstack_values' in obj:
            if u'pc' in obj[u'itemstack_values']:
                inventory = self._localPlayer.Inventory
                for k, v in obj[u'itemstack_values'][u'pc'].iteritems():
                    item = inventory.GetItemById(k)
                    if item:
                        if v[u'class_tsid'] == 'DELETED':
                            event = ItemDeletedEvent(inventory.GetItemById(k))
                            inventory._RemoveItem(k)
                            self.QueueEvent(event)
                        else:
                            event = None
                            if v[u'count'] != inventory.GetItemById(k).Count:
                                event = ItemCountChangedEvent(inventory.GetItemById(k), inventory.GetItemById(k).Count)
                            item._UpdateItem(v)
                            if event:
                                self.QueueEvent(event)
                        #print("Updated item " + k)
                    else:
                        item = CreateItem(v, k)
                        inventory._AddItem(item)
                        event = ItemAddedEvent(item)
                        self.QueueEvent(event)
                        #print("New item " + k)
            elif u'location' in obj[u'itemstack_values']:
                self._activeLocation._UpdateEntites(obj[u'itemstack_values'][u'location'])
    
