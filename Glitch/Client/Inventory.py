from Glitch.Events.Item import VerbQueryEvent, VerbActionEvent, TeleportationScriptCreateEvent, NoteCreateEvent
import Glitch.Events.WorldEvents
import Glitch.Events.Item
import Glitch.Events.Crafting

def RequestRecipe(client, *args):
    packetParams = {'class_tsids' : args}
    return client.SendPacket('recipe_request', packetParams)


class Item(object):
    def __init__(self, itemObject, itemId):
        self._count = itemObject[u'count']
        self._id = itemId
        self._slot = itemObject[u'slot']
        self._version = itemObject[u'version']
        self._classId = itemObject[u'class_tsid']
        self._path = itemObject[u'path_tsid'].split('/')
        self._label = itemObject[u'label']
        self._tooltipLabel = None
        if u'tooltip_label' in itemObject:
            self._tooltipLabel = itemObject[u'tooltip_label']
            
    def QueryVerbList(self, client, data = None):
        return client.SendPacket('itemstack_verb_menu', {'starting_menu' : True, 'itemstack_tsid' : self._id}, callbackFn = self._QueryVerbListCallback, callbackArgs = (client,), userData = data)
        
    def DoVerb(self, client, verb, count = 1, extraArgs = {}, data = None):
        args = {'itemstack_tsid' : self._id, 'count' : count, 'verb' : verb}
        args.update(extraArgs)
        return client.SendPacket('itemstack_verb', args, callbackFn = self._DoVerbCallback, callbackArgs = (client, verb), userData = data)
    
    def Craft(self, client, verb, recipeId, count = 1):
        return client.SendPacket('make_known', {'itemstack_tsid' : self._id, 'count' : count, 'verb' : verb, 'recipe' : recipeId}, callbackFn = self._MakeKnownCallback, callbackArgs = (client, verb))
    
    def Move(self, client, destContainerId = None, destSlot = None):
        args = {'itemstack_tsid': self.Id}
        if self.ParentContainer:
            args[u'from_path_tsid'] = self.ParentContainer
        if destContainerId:
            args[u'to_path_tsid'] = destContainerId
        if destSlot:
            args[u'to_slot'] = destSlot
        return client.SendPacket('inventory_move', args, callbackFn = self._MoveCallback, callbackArgs = (client,))
    
    def QueryInventoryDropTargets(self, client):
        return client.SendPacket('inventory_drop_targets', {'itemstack_tsid': self.Id}, callbackFn = self._DropTargetCallback, callbackArgs = (client,))
    
    def QueryLocationDropTargets(self, client):
        return client.SendPacket('location_drop_targets', {'itemstack_tsid': self.Id}, callbackFn = self._DropTargetCallback, callbackArgs = (client,))
    
    @property
    def Count(self):
        return self._count
    
    @property
    def Id(self):
        return self._id
    
    @property
    def Slot(self):
        return self._slot
    
    @property
    def ClassId(self):
        return self._classId
    
    @property
    def ParentContainer(self):
        if len(self._path) > 1:
            return self._path[len(self._path) - 2]
        else:
            return None
        
    @property
    def Label(self):
        return self._label
    
    @property
    def TooltipLabel(self):
        return self._tooltipLabel
    
    def _UpdateItem(self, updateObject):
        if u'count' in updateObject:
            self._count = updateObject[u'count']
        if u'slot' in updateObject:
            self._slot = updateObject[u'slot']
        if u'version' in updateObject:
            self._version = updateObject[u'version']
        if u'class_tsid' in updateObject:
            self._classId = updateObject[u'class_tsid']
        if u'path_tsid' in updateObject:
            self._path = updateObject[u'path_tsid'].split('/')
        if u'label' in updateObject:
            self._label = updateObject[u'label']
        if u'tooltip_label' in updateObject:
            self._tooltipLabel = updateObject[u'tooltip_label']
    
    def _QueryVerbListCallback(self, packet, client):
        event = VerbQueryEvent(packet.packetObject[u'itemDef'], self)
        client.QueueEvent(event)
        
    def _DoVerbCallback(self, packet, client, verb):
        event = VerbActionEvent(packet.packetObject, self, verb)
        client.QueueEvent(event)
        
    def _MoveCallback(self, packet, client):
        event = Glitch.Events.Item.ItemMoveEvent(packet.packetObject, self)
        client.QueueEvent(event)
        
    def _DropTargetCallback(self, packet, client):
        event = Glitch.Events.Item.DropTargetEvent(packet.packetObject, self)
        client.QueueEvent(event)
        
    def _MakeKnownCallback(self, packet, client, verb):
        event = Glitch.Events.Crafting.CraftingBeginEvent(packet.packetObject, self, verb)
        client.QueueEvent(event)
    
class ToolItem(Item):
    def __init__(self, itemObject, itemId):
        super(ToolItem, self).__init__(itemObject, itemId)
        self._isBroken = itemObject[u'tool_state'][u'is_broken']
        self._durability = None
        if u'points_remaining' in itemObject[u'tool_state']:
            self._durability = itemObject[u'tool_state'][u'points_remaining']
        self._maxDurability = None
        if u'points_capacity' in itemObject[u'tool_state']:
            self._maxDurability = itemObject[u'tool_state'][u'points_capacity']
        
    @property
    def IsBroken(self):
        return self._isBroken
    
    @property
    def Durability(self):
        return self._durability
    
    @property
    def MaxDurability(self):
        return self._maxDurability
    
    def _UpdateItem(self, updateObject):
        super(ToolItem, self)._UpdateItem(updateObject)
        if u'tool_state' in updateObject:
            if u'is_broken' in updateObject[u'tool_state']:
                self._isBroken = updateObject[u'tool_state'][u'is_broken']
            if u'points_remaining' in updateObject[u'tool_state']:
                self._durability = updateObject[u'tool_state'][u'points_remaining']
            if u'points_capacity' in updateObject[u'tool_state']:
                self._maxDurability = updateObject[u'tool_state'][u'points_capacity']

class Container(Item):
    def __init__(self, itemObject, itemId):
        super(Container, self).__init__(itemObject, itemId)
        self._slots = itemObject[u'slots']
                
    @property
    def Slots(self):
        return self._slots
    
    def _UpdateItem(self, updateObject):
        super(Container, self)._UpdateItem(updateObject)   
        if u'slots' in updateObject:
            self._slots = updateObject[u'slots']        
    
class TeleportationScript(Item):
    def __init__(self, itemObject, itemId):
        super(TeleportationScript, self).__init__(itemObject, itemId)
    
    def Use(self, client, useToken = False):
        client.SendPacket('teleportation_script_use', {'use_token': useToken, 'itemstack_tsid': self.Id}, callbackFn = self._UseCallback, callbackArgs = (client,))
        
    def Read(self, client):
        self.DoVerb(client, 'read', 1)
        
    def _UseCallback(self, packet, client):
        fromLocation = client.ActiveLocation
        event = Glitch.Events.WorldEvents.TeleportScriptUseEvent(packet.packetObject, fromLocation, self)
        client.QueueEvent(event)
        
class Paper(Item):
    def __init__(self, itemObject, itemId):
        super(Paper, self).__init__(itemObject, itemId)
    
    def WriteTeleportationScript(self, client, imbue = False):
        return client.SendPacket('teleportation_script_create', {'is_imbued': imbue, 'itemstack_tsid': self.Id}, callbackFn = self._ScriptWrittenCallback, callbackArgs = (client,))
        
    def WriteNote(self, client, title, body):
        return client.SendPacket('note_save', {'body': body, 'title': title, 'itemstack_tsid': self._id}, callbackFn = self._NoteWrittenCallback, callbackArgs = (client,))
        
    def _ScriptWrittenCallback(self, packet, client):
        event = TeleportationScriptCreateEvent(packet.packetObject)
        client.QueueEvent(event)
        
    def _NoteWrittenCallback(self, packet, client):
        item = None
        if u'changes' in packet.packetObject:
            for k, v in packet.packetObject[u'changes'][u'itemstack_values'][u'pc'].iteritems():
                if v[u'class_tsid'] == 'note':
                    item = client._localPlayer.Inventory.GetItemById(k)
        event = NoteCreateEvent(packet.packetObject, item)
        client.QueueEvent(event)

class Inventory(object):
    def __init__(self, inventoryObject = None):
        self._items = []
        if inventoryObject:
            for k, v in inventoryObject.iteritems():
                item = CreateItem(v, k)
                self._items.append(item)
                
    def __len__(self):
        return len(self._items)
    
    def __iter__(self):
        for i in self._items:
            yield i
            
    def GetBagContents(self, bag):
        items = []
        for item in self._items:
            if item.ParentContainer == bag.Id:
                items.append(item)
                
        return items
    
    def GetFreeSlotsInContainer(self, container):
        slots = container.Slots
        for item in self._items:
            if item.ParentContainer == container.Id:
                slots -= 1
        
        return slots
    
    def GetFreeSlotsInContainersByClassId(self, *args):
        bags = {}
        for item in self._items:
            for arg in args:
                if item.ParentContainer == None and hasattr(item, 'Slots') and item.ClassId == arg:
                    bags[item.Id] = [item.Slots, 0]
        slots = 0
        
        for item in self._items:
            if item.ParentContainer in bags:
                bags[item.ParentContainer][1] += 1
        
        for v in bags.itervalues():
            slots += v[0] - v[1]
                
        return slots
        
    
    def GetTotalFreeSlots(self):
        bags = {}
        for item in self._items:
            if item.ParentContainer == None and hasattr(item, 'Slots'):
                bags[item.Id] = [item.Slots, 0]
        
        slots = 0
        
        for item in self._items:
            if item.ParentContainer in bags:
                bags[item.ParentContainer][1] += 1
        
        for v in bags.itervalues():
            slots += v[0] - v[1]
                
        return slots
    
    def GetItemsByLabel(self, label):
        itemMatches = []
        for item in self._items:
            if item.Label == label:
                itemMatches.append(item)
        return itemMatches
    
    #def GetItemsByClassId(self, classId):
    #    itemMatches = []
    #    for item in self._items:
    #        if item.ClassId == classId:
    #            itemMatches.append(item)
    #    return itemMatches
    
    def GetItemsByClassId(self, *args):
        itemMatches = []
        for item in self._items:
            for matchId in args:
                if item.ClassId == matchId:
                    itemMatches.append(item)
        return itemMatches
    
    def GetItemById(self, itemId):
        for item in self._items:
            if item.Id == itemId:
                return item

    def GetItemInSlot(self, slot, container = None):
        for item in self._items:
            if item.ParentContainer == container and item.Slot == slot:
                return item
    
    def GetItemsInContainer(self, container):
        itemMatches = []
        for item in self._items:
            if item.Container == container:
                itemMatches.append(item)
        return itemMatches
    
    def CountAllByClassId(self, classId):
        count = 0
        for item in self._items:
            if item.ClassId == classId:
                count += item.Count
        return count
    
    def CountAllByLabel(self, label):
        count = 0
        for item in self._items:
            if item.Label == label:
                count += item.Count
        return count
    
    def _RemoveItem(self, itemId):
        for item in self._items:
            if item.Id == itemId:
                self._items.remove(item)
                break
            
    def _AddItem(self, item):
        self._items.append(item)
            

def CreateItem(itemObj, itemName):
    if itemObj[u'class_tsid'] == 'paper':
        return Paper(itemObj, itemName)
    elif itemObj[u'class_tsid'] == 'teleportation_script':
        return TeleportationScript(itemObj, itemName)
    if u'slots' in itemObj:
        return Container(itemObj, itemName)
    if u'tool_state' in itemObj:
        return ToolItem(itemObj, itemName)
    else:
        return Item(itemObj, itemName)
        