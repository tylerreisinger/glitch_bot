'''
Created on Apr 16, 2012

@author: tyler
'''

from Glitch.Events.Event import Event

class CraftingRecipe(object):
    def __init__(self, idNum, obj):
        self._id = idNum
        self._name = obj[u'name']
        self._waitMs = obj[u'wait_ms']
        self._tool = obj[u'tool']
        self._energyCost = obj[u'energy_cost']
        self._toolVerb = obj[u'tool_verb']
        self._taskLimit = obj[u'task_limit']
        self._xpReward = obj[u'xp_reward']
        self._inputs = []
        for i in obj[u'inputs']:
            self._inputs.append((i[0], i[1]))
            
    @property
    def Id(self):
        return self._id
    
    @property
    def Name(self):
        return self._name
    
    @property
    def WaitMs(self):
        return self._waitMs
    
    @property
    def Tool(self):
        return self._tool
    
    @property
    def EnergyCost(self):
        return self._energyCost
    
    @property
    def ToolVerb(self):
        return self._toolVerb
    
    @property
    def TaskLimit(self):
        return self._taskLimit
    
    @property
    def XpReward(self):
        return self._xpReward
    
    @property
    def Inputs(self):
        return self._inputs

class CraftingStartEvent(Event):
    def __init__(self, obj):
        self._itemId = obj[u'item_tsid']
        self._slots = obj[u'slots']
        self._verb = obj[u'verb']
        self._knownRecipes = {}
        for k, v in obj[u'knowns'].iteritems():
            Recipe = CraftingRecipe(k, v)
            self._knownRecipes[v[u'name']] = Recipe
        Event.__init__(self)
        
    @property
    def CraftingItemId(self):
        return self._itemId
    
    @property
    def Slots(self):
        return self._slots
    
    @property
    def Verb(self):
        return self._verb
    
    @property
    def Recipes(self):
        return self._knownRecipes
    
class CraftingBeginEvent(Event):
    def __init__(self, obj, item, verb):
        self._success = obj[u'success']
        self._wait = 0
        self._item = item
        self._verb = verb
        if u'wait' in obj:
            self._wait = obj[u'wait']
        Event.__init__(self)
    
    @property
    def Succeess(self):
        return self._success
    
    @property
    def WaitTime(self):
        return self._wait
    
    @property
    def Item(self):
        return self._item
    
    @property
    def Verb(self):
        return self._verb
    
class CraftingEndEvent(Event):
    def __init__(self, obj):
        self._overXpLimit = obj[u'over_xp_limit']
        self._energyChange = 0
        self._xpChange = 0
        if u'effects' in obj:
            if u'energy' in obj[u'effects']:
                self._energyChange = obj[u'effects'][u'energy']
            if u'xp' in obj[u'effects']:
                self._xpChange = obj[u'effects'][u'xp']
        Event.__init__(self)
                
    @property
    def OverXpLimit(self):
        return self._overXpLimit
    
    @property
    def EnergyChange(self):
        return self._energyChange

    @property
    def XpChange(self):
        return self._xpChange
    
class RecipeRequestEvent(Event):
    def __init__(self, packetObj):
        self._success = packetObj[u'success']
        self._recipes = {}
        for k, v in packetObj.iteritems():
            if k != u'success' and k != u'msg_id' and k != u'type':
                if len(v) == 0:
                    self._recipes[k] = None
                else:
                    self._recipes[k] = CraftingRecipe(v)
                    
    @property
    def Success(self):
        return self._success
    
    @property
    def Recipes(self):
        return self._recipes