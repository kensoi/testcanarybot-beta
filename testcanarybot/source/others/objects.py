from .enums import events as enums_events
from .values import expression

from datetime import datetime
import aiohttp
import threading
import asyncio
import random
import typing
import sqlite3


class mention:
    __slots__ = ('id', 'call') 
    def __init__(self, page_id, mention = ""):
        self.id = page_id
        self.call = mention

    def __int__(self):
        return self.id 

    def __str__(self):
        return self.call    
    

class database:
    def __init__(self, directory):
        self.directory = 'assets/' + directory
        self.connection = sqlite3.connect(self.directory)
        self.cursor = self.connection.cursor()


    def request(self, request: str):
        self.cursor.execute(request)
        self.connection.commit()
        
        return self.cursor.fetchall()


    def close(self):
        self.connection.close()


class data:
    def __init__(self, **entries):
        self.__dict__.update(entries)

        for i in self.__dict__.keys():
            setattr(self, i, self.__convert(getattr(self, i)))
        self.raw = entries
            

    def __convert(self, attr):
        attr_type = type(attr)

        if attr_type == dict:
            return key(**attr)

        elif attr_type == list:
            return [self.__convert(i) for i in attr]
        
        else:
            return attr    


class key(data):
    pass

class package(data):
    __item = "$item"
    __items = "$items"
    __mention = "$mention"
    __mentions = "$mentions"
    __expr = "$expr"
    __exprs = "$exprs"

    id = 0
    date = 0
    random_id = 0
    peer_id = 1
    from_id = 1
    items = []

    class params:
        action = False
        attachments = False
        payload = False
        command = False
        from_chat = False
        gment = ""
        mentions = []
        key_start = 0


    type = ''


    def getItems(self):
        return self.items[:-1]
            

    def check(self, command: list) -> typing.Union[bool, list]:
        """
        Following keys:
        $item - any string
        $items - any string
        $expr - expression item
        $exprs - list from this item to the end is a list of expression objects
        $mention - mention item
        $mentions - list from this item to the end is a list of mention objects
        """
        if len(self.items) == 0:
            return False
        
        if command[-1] not in [self.__mentions, self.__exprs, self.__items]:
            if len(command) + 1 != len(self.items): 
                return False

        for i in range(len(command)):
            if command[i] == self.items[i]:
                continue
                
            elif command[i] == self.__item:
                if not isinstance(self.items[i], str):
                    return False
                continue

            elif command[i] == self.__items:
                return self.items[i:-1]

            elif command[i] == self.__expr:
                if not isinstance(self.items[i], (expression, str)):
                    return False
                continue

            elif command[i] == self.__mention:
                if not isinstance(self.items[i], mention):
                    return False
                continue

            elif command[i] == self.__exprs:
                if not isinstance(j, expression):
                    return False
                return self.items[i:-1]

            elif command[i] == self.__mentions:
                mentions = 0
                for j in self.items[i:-1]:
                    if not isinstance(j, (mention, str)):
                        return False
                    mentions += 1

                if mentions > 1:
                    return self.items[i:-1]
                else:
                    return False

            else:
                return False
            
        return True
            

def WaitReply(packagetest):
    return f"${packagetest.peer_id}_{packagetest.from_id}"


class libraryModule:
    codename = "testcanarybot_module"
    name = "testcanarybot sample module"
    description = "http://kensoi.github.io/testcanarybot/createmodule.html"
    packagetype = []

    def __init__(self):
        self.commands = []
        self.handler_dict = {}
        self.void_react = False
        self.event_handlers = {} # event.abstract_event: []

    def registerCommand(self, ):
        pass


def event(events: list):
    def decorator(coro: asyncio.coroutine):
        def registerCommand(self, *args, **kwargs):
            try:
                if coro.__name__ in ['package_handler', 'priority', 'void', 'event']:
                    raise TypeError("Incorrect coroutine registered as command handler!")

                else:
                    for i in events:
                        if not isinstance(i, enums_events):
                            raise TypeError("Incorrect type!")

                        elif i not in self.event_handlers and i != enums_events.message_new:
                            self.event_handlers[i] = []

                        self.event_handlers[i].append(coro)
                return # coro(self, *args, **kwargs)
            except Exception as e:
                print(e)
            
        return registerCommand
    return decorator


def priority(commands: list): 
    def decorator(coro: typing.Generator):
        def registerCommand(self: libraryModule, *args, **kwargs):
            if coro.__name__ in ['package_handler', 'priority', 'void', 'event']:
                raise TypeError("Incorrect coroutine registered as priority handler!")

            else:
                self.commands.extend(commands)

                self.handler_dict[coro.__name__] = {'handler': coro, 'commands': commands}
            return # coro(self, *args, **kwargs)
        return registerCommand
    return decorator


def void(coro: typing.Generator):
    def registerCommand(self: libraryModule, *args, **kwargs):
        if coro.__name__ in ['package_handler', 'priority', 'void', 'event']:
            raise TypeError("Incorrect coroutine registered as void handler!")

        else:
            self.void_react = coro

        return # coro(self, *args, **kwargs)
    return registerCommand



class tools:
    """
    sampled tools object
    """
    class api:
        pass
    http = object()

    mentions = list()
    mentions_name_cases = []

    group_id = 0
    name_cases = [
            'nom', 'gen', 
            'dat', 'acc', 
            'ins', 'abl'
            ]

    mentions_self = {
        'nom': 'я', 
        'gen': ['меня', 'себя'],
        'dat': ['мне', 'себе'],
        'acc': ['меня', 'себя'],
        'ins': ['мной', 'собой'],
        'abl': ['мне','себе'],
    }
    mentions_unknown = {
        'all': 'всех',
        'him': 'его',
        'her': 'её',
        'it': 'это',
        'they': 'их',
        'them': 'их',
        'us': 'нас',
        'everyone': ['@everyone', '@all', '@все']
    }

    def get(self, db_name: str) -> database:
        pass


    def system_message(self, *args, textToPrint = None, module = None, newline = False) -> None:
        pass


    def random_id(self) -> int:
        return random.randint(0, 99999999)


    def ischecktype(self, checklist, checktype) -> bool:
        for i in checklist:
            if isinstance(checktype, list) and type(i) in checktype:
                return True
                
            elif isinstance(checktype, type) and isinstance(i, checktype): 
                return True
            
        return False


    def getDate(self, time = None) -> str:
        if not time: time = datetime.now()
        return f'{"%02d" % time.day}.{"%02d" % time.month}.{time.year}'
    
    
    def getTime(self, time = None) -> str:
        if not time: time = datetime.now()
        return f'{"%02d" % time.hour}:{"%02d" % time.minute}:{"%02d" % time.second}.{time.microsecond}'


    def getDateTime(self, time = None) -> str:
        if not time: time = datetime.now()
        return self.getDate(time) + ' ' + self.getTime(time)


    def makepages(self, obj:list, page_lenght: int = 5, listitem: bool = False):
        pass


    def add(self, db_name: str) -> None:
        pass


    async def getMention(self, page_id: int, name_case = "nom") -> str:
        pass


    async def getManagers(self, group_id = None) -> list:
        pass


    async def isManager(self, from_id: int, group_id = None) -> bool:
        pass


    async def getChatManagers(self, peer_id: int) -> list:
        pass
        

    def isChatManager(self, from_id, peer_id: int) -> bool:
        pass


    async def getMembers(self, peer_id: int) -> list:
        pass


    async def isMember(self, from_id: int, peer_id: int) -> bool:
        pass


    def parse_mention(self, ment) -> mention:
        page_id, call = ment[0: ment.find('|')], ment[ment.find('|') + 1:]

        page_id = page_id.replace('id', '')
        page_id = page_id.replace('club', '-')
        page_id = page_id.replace('public', '-')
            
        return mention(int(page_id), call)


    def parse_link(self, link) -> str:
        response = link

        response.replace('https://', '')
        response.replace('http://', '')
        
        return response
