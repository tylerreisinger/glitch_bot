'''
Created on Apr 16, 2012

@author: tyler
'''

from Glitch.Events.Event import Event

class VerbDefinition(object):
    def __init__(self, verbName, verbObject):
        self._name = verbName
        self._verbObject = verbObject
        
    @property
    def Name(self):
        return self._name
    
    @property
    def IsEnabled(self):
        return self._verbObject[u'enabled']
    
    @property
    def Label(self):
        return self._verbObject[u'label']
    
    @property
    def IsDefault(self):
        return self._verbObject[u'is_default']
    
    @property
    def DisabledReason(self):
        if not self.IsEnabled():
            return self._verbObject[u'disabled_reason']
        return ''
    
    @property
    def RequiresTargetItem(self):
        return self._verbObject[u'requires_target_item']
    
    @property
    def RequiresTargetPlayer(self):
        return self._verbObject[u'requires_target_pc']

class VerbQueryEvent(Event):
    def __init__(self, itemDef, item):
        super(VerbQueryEvent, self).__init__()
        self._classId = itemDef[u'class_tsid']
        self._verbs = {}
        self._item = item
        for k, v in itemDef[u'verbs'].iteritems():
            verb = VerbDefinition(k, v)
            self._verbs[k] = verb
            
    @property
    def Item(self):
        return self._item
            
    @property
    def ItemClassId(self):
        return self._classId
    
    @property
    def Verbs(self):
        return self._verbs
    
    def GetVerb(self, name):
        if name in self._verbs:
            return self._verbs[name]
        
    def ContainsVerb(self, name):
        if name in self._verbs:
            return True
        else:
            return False

class VerbActionEvent(Event):
    def __init__(self, obj, item, verb):
        super(VerbActionEvent, self).__init__()
        self._success = obj[u'success']
        self._item = item
        self._verb = verb
        
    @property
    def Success(self):
        return self._success
    
    @property
    def Item(self):
        return self._item
    
    @property
    def Verb(self):
        return self._verb
    
class ItemAddedEvent(Event):
    def __init__(self, item):
        super(ItemAddedEvent, self).__init__()
        self._item = item
        
    @property
    def Item(self):
        return self._item

class ItemDeletedEvent(Event):
    def __init__(self, item):
        super(ItemDeletedEvent, self).__init__()
        self._item = item

    @property
    def Item(self):
        return self._item

class ItemCountChangedEvent(Event):
    def __init__(self, item, oldCount):
        super(ItemCountChangedEvent, self).__init__()
        self._item = item
        self._oldCount = oldCount

    @property
    def Item(self):
        return self._item
    
    @property
    def OldItemCount(self):
        return self._oldCount
    
class TeleportationScriptReadEvent(Event):
    def __init__(self, packetObj, item):
        super(TeleportationScriptReadEvent, self).__init__()
        self._success = packetObj[u'success']
        self._item = item
        self._destinationId = packetObj[u'destination']
        self._isImbued = packetObj[u'is_imbued']
        self._body = packetObj[u'body']
    
    @property
    def Success(self):
        return self._success
    
    @property
    def Item(self):
        return self._item
    
    @property
    def DestinationId(self):
        return self._destinationId
    
    @property
    def IsImbued(self):
        return self._isImbued
    
    @property
    def Body(self):
        return self._body
    
class TeleportationScriptCreateEvent(Event):
    def __init__(self, packetObj):
        super(TeleportationScriptCreateEvent, self).__init__()
        self._success = packetObj[u'success']
    
    @property
    def Success(self):
        return self._success
    
class NoteCreateEvent(Event):
    def __init__(self, packetObj, item):
        super(NoteCreateEvent, self).__init__()
        self._success = packetObj[u'success']
        self._item = item
    
    @property
    def Success(self):
        return self._success
    
    @property
    def Item(self):
        return self._item
    
class NoteReadEvent(Event):
    def __init__(self, packetObj, item):
        super(NoteReadEvent, self).__init__()
        self._title = None
        self._body = None
        self._item = item
        self._authorName = None
        self._authorId = None
        self._title = packetObj[u'title']
        self._body = packetObj[u'body']
        if u'pc' in packetObj:
            self._authorId = packetObj[u'pc'][u'tsid']
            self._authorName = packetObj[u'pc'][u'label']
    
    @property
    def Title(self):
        return self._title
    
    @property
    def Body(self):
        return self._body
    
    @property
    def Item(self):
        return self._item
    
    @property
    def AuthorId(self):
        return self._authorId
    
    @property
    def AuthorName(self):
        return self._authorName
    
class ItemMoveEvent(Event):
    def __init__(self, packetObj, item):
        super(ItemMoveEvent, self).__init__()
        self._success = packetObj[u'success']
        self._item = item
        
    @property
    def Success(self):
        return self._success
    
    @property
    def Item(self):
        return self._item
    
class ItemDropTarget(object):
    def __init__(self, obj, itemId):
        self._disabled = obj[u'disabled']
        self._verb = obj[u'verb']
        self._justOne = obj[u'just_one']
        self._toolTip = obj[u'tip']
        self._id = itemId
        
    @property
    def Id(self):
        return self._id
        
    @property
    def Disabled(self):
        return self._disabled
    
    @property
    def Verb(self):
        return self._verb
    
    @property
    def JustOne(self):
        return self._justOne
    
    @property
    def ToolTip(self):
        return self._toolTip
    
class DropTargetEvent(Event):
    def __init__(self, packetObj, item):
        super(DropTargetEvent, self).__init__()
        self._success = packetObj[u'success']
        self._item = item
        self._bags = []
        self._itemstacks = []
        self._cabinets = []
        if u'bags' in packetObj:
            for bag in packetObj[u'bags']:
                self._bags.append(bag)
            for cabinet in packetObj[u'cabinets']:
                self._cabinets.append(cabinet)
            for k, v in packetObj[u'itemstacks'].iteritems():
                self._itemstacks.append(ItemDropTarget(v, k))
                
    @property
    def Success(self):
        return self._success
    
    @property
    def Item(self):
        return self._item
    
    @property
    def Bags(self):
        return self._bags
    
    @property
    def Itemstacks(self):
        return self._itemstacks
    
    @property
    def Cabinets(self):
        return self._cabinets
            