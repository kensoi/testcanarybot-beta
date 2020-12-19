import asyncio
import importlib
import os
import random
import six
import sqlite3
import threading
import traceback


from .events import events
from .versions_list import static

from . import objects
from datetime import datetime
from .expressions import expressions, setExpression, Pages

class _assets:
    def __init__(self):
        self.path = os.getcwd() + '\\assets\\'

    def __call__(self, *args, **kwargs):
        args = list(args)
        if len(args) > 0:
            args[0] = self.path + args[0]
        
        elif 'file' in kwargs:
            kwargs['file'] = self.path + kwargs['file']
        
        return open(*args, **kwargs)

    def __exit__(self, exc_type, exc_value, traceback):
        pass

assets = _assets()

class handler(threading.Thread):
    processing = False

    def __init__(self, library, handler_id):
        threading.Thread.__init__(self)
        self.thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.thread_loop)
        self.daemon = True
        self.handler_id = handler_id

        self.library = library
        self.event = None


    def run(self):
        self.setName(f"handler_{self.handler_id}")
        self.library.tools.system_message(f"{self.getName()} is started", module = "message_handler")
        while True:
            if self.event: 
                self.processing = True
                self.parse_event(self.event)
                self.event = None
                self.processing = False


    def parse_event(self, event):
        if isinstance(event, dict):
            if hasattr(events, event['type']):
                event_type = getattr(events, event['type'])

                if event_type == events.message_new:
                    package = objects.message(**event['object']['message'])
                    package.items = []

                    if hasattr(package, 'action'): 
                        package.items.append(self.library.tools.getValue("ACTION"))
                    
                    elif hasattr(package, 'payload'):
                        package.items.append(self.library.tools.getValue("PAYLOAD"))
                        package.payload = json.loads(package.payload)

                    elif package.text != '': 
                        package.items, package.mentions = self.parse_command(package.text)

                    elif len(package.attachments) > 0: 
                        package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                        
                    not_command = len(package.items) == 0
                    only_commands = self.library.tools.getValue("ONLY_COMMANDS").value

                    if not only_commands or not not_command: 
                        if not_command: package.items.append(self.library.tools.getValue("NOT_COMMAND"))
                        
                        package.items.append(self.library.tools.getValue("ENDLINE"))
                        self.parse_package(package)

                else:
                    package = objects.package(**event['object'])
                    package.type = event_type

                    for key, value in event['object'].items():
                        if key in _ohr.peer_id: package.peer_id = value
                        if key in _ohr.from_id: package.from_id = value

                    self.parse_package(package)  

        elif issubclass(type(self.event), objects.Object):
            package = self.event
            if package.type == events.message_new:

                if hasattr(package, 'action'): 
                    package.items.append(self.library.tools.getValue("ACTION"))
                
                elif hasattr(package, 'payload'):
                    package.items.append(self.library.tools.getValue("PAYLOAD"))
                    package.payload = json.loads(package.payload)

                elif package.text != '': 
                    package.items, package.mentions = self.parse_command(package.text)

                elif len(package.attachments) > 0: 
                    package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                    
                package.items.append(self.library.tools.getValue("ENDLINE"))
                if not self.library.tools.getValue("ONLY_COMMANDS").value:
                    self.parse_package(package)

            else:
                for key, value in event['object'].items():
                    if key in _ohr.peer_id: package.peer_id = value
                    if key in _ohr.from_id: package.from_id = value

                self.parse_package(package)


    def parse_command(self, messagetoreact):
        response, mentions = [], []
        message = messagetoreact.split() 

        if len(message) > 1:
            if message[0] in [*self.library.tools.getValue("MENTIONS").value]:
                message.pop(0)
                message_lenght = len(message)
                i = 0
                while i != message_lenght:
                    if message[i][0] == '[' and message[i].count('|') == 1:
                        if message[i].count(']') > 0:
                            mention = self.library.tools.parse_mention(
                                    message[i][message[i].rfind('[') + 1:message[i].find(']')]
                                    )
                            mentions.append(mention)
                            response.append(
                                mention
                                )
                        else:
                            for j in range(i, message_lenght):
                                if message[j].count(']') > 0:
                                    last_string, message[j] = message[j][0:message[j].find(']')], message[j][message[j].find(']') + 1:]
                                    mention = " ".join([*message[i:j], last_string])[1:]
                                    mention = self.library.tools.parse_mention(
                                            mention
                                            )
                                    response.append(mention)
                                    mentions.append(mention)
                                    response.append(message[j])
                                    i = j
                                    break
                    else:
                        response.append(message[i])

                    i += 1

            if len(response) != 0:
                return response, mentions
        
        if self.library.tools.getValue("ADD_MENTIONS").value:
            message_lenght = len(message)
            i = 0
            ment_obj = self.library.tools.getValue("MENTION")
            while i != message_lenght:
                if message[i].lower() in [*self.library.tools.getValue("MENTIONS").value, 
                                    *self.library.tools.getValue("MENTION_NAME_CASES").value] and len(response) == 0: 
                    response = [ment_obj]

                if message[i][0] == '[' and message[i].count('|') == 1:
                    if message[i].count(']') > 0:
                        mention = self.library.tools.parse_mention(
                                message[i][message[i].rfind('[') + 1:message[i].find(']')]
                                )
                        mentions.append(mention)
                    else:
                        for j in range(i, message_lenght):
                            if message[j].count(']') > 0:
                                last_string, message[j] = message[j][0:message[j].find(']')], message[j][message[j].find(']') + 1:]
                                mention = " ".join([*message[i:j], last_string])[1:]
                                mention = self.library.tools.parse_mention(
                                        mention
                                        )
                                mentions.append(mention)
                                i = j
                                break
                    
                i += 1

            if len(response) != 0:
                return response, mentions

        return [], []


    def parse_package(self, event_package):
        if (not self.library.tools.getValue("ONLY_COMMANDS")) == (len(event_package.items) == 1):
            if event_package.type in self.library.event_supports.keys():
                itemscopy = event_package.items.copy()
                modules = [asyncio.ensure_future(self.library.modules[i].package_handler(self.library.tools, event_package), loop = self.thread_loop) for i in self.library.event_supports[event_package.type]]
                        
                reaction = filter(
                    lambda i: i != None, 
                    self.thread_loop.run_until_complete(asyncio.gather(*modules)))
                reaction = list(reaction)

                if len(self.library.error_handlers) > 0:
                    if len(reaction) == 0:
                        reaction.append([self.library.tools.getValue("NOREACT")])
                        
                    for i in reaction:
                        if isinstance(i, (list, tuple)):
                            if isinstance(i, tuple): i = list(i)
                            event_package.items = i

                            try:
                                if event_package.items[0] == self.library.tools.getValue("LIBRARY"):
                                    if event_package.items[1] == self.library.tools.getValue("LIBRARY_NOSELECT"):
                                        event_package.items[1] = [
                                            (e, self.library.modules[e].name) for e in self.library.modules.keys() if e not in self.library.hidden_modules
                                        ]

                                    elif event_package.items[1] == self.library.tools.getValue("LIBRARY_RELOAD"):
                                        self.library.upload(isReload = True, loop = self.thread_loop)
                                        event_package.items.append(self.library.tools.getValue("LIBRARY_SUCCESS"))

                                    elif event_package.items[1] in self.library.modules.keys():
                                        event_package.items.append(self.library.modules[event_package.items[1]].version)
                                        event_package.items.append(self.library.modules[event_package.items[1]].description)

                                    else:
                                        event_package.items[1] = self.library.tools.getValue("LIBRARY_ERROR")

                                    eh = [asyncio.ensure_future(self.library.modules[i].error_handler(self.library.tools, event_package), loop = self.thread_loop) for i in self.library.error_handlers]
                                    
                                    self.library.tools.module = 'error_handler'
                                    self.thread_loop.run_until_complete(asyncio.wait(eh))

                            except Exception as e:
                                self.library.tools.system_message(traceback.format_exc())
                    
                response = self.library.tools.getValue("MESSAGE_HANDLER_TYPE").value + '\n'
                if event_package.peer_id != event_package.from_id:
                    response += self.library.tools.getValue("MESSAGE_HANDLER_CHAT").value + '\n'

                response += self.library.tools.getValue("MESSAGE_HANDLER_USER").value + '\n'
                if self.library.tools.getValue("NOT_COMMAND") not in itemscopy and self.library.tools.ischecktype(itemscopy, objects.expression):
                    response += self.library.tools.getValue("MESSAGE_HANDLER_ITEMS").value + '\n'
                    itemscopy = [str(i) for i in itemscopy[:-1]]
                if event_package.text !='': response += self.library.tools.getValue("MESSAGE_HANDLER_IT").value + '\n'
                
                response = response.format(
                    peer_id = event_package.peer_id,
                    from_id = event_package.from_id,
                    event_type = event_package.type.value,
                    items = itemscopy,
                    text = "\t" + event_package.text.replace("\n", "\n\t\t\t")
                )
                self.library.tools.system_message(response, module = "message_handler")


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


class databases:
    def __init__(self, names: list):
        self.upload(names)


    def check(self, name):
        response = [*self.__dbs.keys(), 
                *[i.directory for i in self.__dbs.values()]]

        return name in response 


    def upload(self, names):
        self.__dbs = {}
        self.add(names)


    def get(self, name):
        check = type(name)
        if check == tuple:
            if not self.check(name[0]):
                raise exceptions.DBError("This DB does not exist")

            else:
                return self.__dbs[name[1]]

        elif check == str:
            if not self.check(name):
                raise exceptions.DBError("This DB does not exist")

            else:
                return self.__dbs[name]



    def add(self, names): 
        check = type(names)

        if check == list:
            for name in names:
                if self.check(name[0]):
                    raise DBError("This DB already exists")

                else:
                    self.__dbs[name[0]] = database(name[1])

        elif check == tuple:
            if self.check(names[0]):
                raise DBError("This DB already exists")

            else:
                self.__dbs[names[0]] = database(names[1])

        elif check == str:
            if self.check(names):
                raise DBError("This DB already exists")

            else:
                self.__dbs[names] = database(names)
        
        else:
            raise DBError("Incorrect type of 'names'")


class library:
    modules = {}
    event_supports = {}

    error_handlers = []
    package_handlers = []
    hidden_modules = []

    needattr = {'name', 'version', 'description'}


    def __init__(self, v, group_id, api, http):
        self.supp_v = v
        self.tools = tools(group_id, api, http)


    def upload(self, isReload = False, loop = asyncio.get_event_loop()):
        self.modules = {}
        if 'library' in os.listdir(os.getcwd()):
            self.tools.system_message(self.tools.getValue("LIBRARY_UPLOADER_GET"), module = "library.uploader")
            
            listdir = os.listdir(os.getcwd() + '\\library\\')
            listdir.remove("__pycache__")
            if len(listdir) == 0:
                raise exceptions.LibraryError(
                    self.__library.tools.getValue("SESSION_LIBRARY_ERROR"))
            
            init_async(
                    asyncio.wait(
                        [
                            loop.create_task(self.moduleload(module, isReload)) for module in listdir
                        ]
                    ), loop = loop
                )
            self.tools.system_message(
                "Supporting event types: {event_types}".format(
                    event_types = "\n".join(["", *["\t\t" + str(i) for i in self.event_supports.keys()], ""])
                ), module = "library.uploader", newline = True)
        
    async def moduleload(self, module_name, isReload):
        module = importlib.import_module("library." + module_name[:-3] if module_name.endswith('.py') else module_name + 'main')
        
        if isReload:
            module = importlib.reload(module)
            
        if module_name[-3:] == '.py': module_name = module_name[:-3]
        if hasattr(module, 'Main'):
            moduleObj = module.Main()
            if hasattr(moduleObj, "start"):
                await moduleObj.start(self.tools)
                
            if not(issubclass(type(moduleObj), objects.libraryModule) or self.needattr & set(dir(moduleObj)) == self.needattr):
                return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                    module = module_name), module = "library.uploader")


        else:
            return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                module = module_name), module = "library.uploader")
        if not isReload:
            if hasattr(moduleObj, 'error_handler'): self.error_handlers.append(module_name)
            if hasattr(moduleObj, 'package_handler'):
                if hasattr(moduleObj, 'packagetype') and len(moduleObj.packagetype) > 0:
                    for package in moduleObj.packagetype:
                        if package not in self.event_supports: self.event_supports[package] = list()
                        self.event_supports[package].append(module_name)

                    self.package_handlers.append(module_name)

                else:
                    return self.tools.system_message(self.tools.getValue("MODULE_FAILED_PACKAGETYPE").value.format(
                        module = module_name), module = "library.uploader")

        if module_name in [*self.error_handlers, *self.package_handlers]:
            self.modules[module_name] = moduleObj
            return self.tools.system_message(self.tools.getValue("MODULE_INIT").value.format(
                module = module_name), module = "library.uploader")

        else:
            return self.tools.system_message(self.tools.getValue("MODULE_FAILED_HANDLERS").value.format(
                module = module_name), module = "library.uploader")


    def getCompactible(self, packagetype):
        if packagetype in self.event_supports:
            return self.event_supports[packagetype]
        else:
            return []


class tools:
    __module = "system_message"
    log = _assets()("log.txt", "a+", encoding="utf-8")
    __db = databases(("system", "system.db"))

    def __init__(self, number, api, http):
        self.group_id = number
        self.api = api
        self.http = http
        init_async(self.__setShort())

        self.group_mention = f'[club{self.group_id}|@{self.group_address}]'
        self.mentions = [self.group_mention]
        self.mentions_name_cases = []
        self.get = self.__db.get



        for print_test in self.getValue("LOGGER_START").value:
            print(print_test, 
                file = self.log
                )
                
        self.log.flush()

        self.name_cases = [
            'nom', 'gen', 
            'dat', 'acc', 
            'ins', 'abl'
            ]
        self.mentions_self = {
            'nom': 'я', 
            'gen': ['меня', 'себя'],
            'dat': ['мне', 'себе'],
            'acc': ['меня', 'себя'],
            'ins': ['мной', 'собой'],
            'abl': ['мне','себе'],
        }
        self.mentions_unknown = {
            'all': 'всех',
            'him': 'его',
            'her': 'её',
            'it': 'это',
            'they': 'их',
            'them': 'их',
            'us': 'нас',
            'everyone': ['@everyone', '@all', '@все']
        }

    
    async def __setShort(self):
        res = await self.api.groups.getById(group_id=self.group_id)
        self.group_address = res[0].screen_name
        return 1


    def system_message(self, *args, textToPrint = None, module = None, newline = False):
        if not module: module = self.__module
        if not textToPrint: textToPrint = " ".join([str(i) for i in list(args)])
        
        response = f'@{self.group_address}.{module}: {textToPrint}'

        if self.log.closed:
            self.log = assets("log.txt", "a+", encoding="utf-8")

        newline_res = "\n" if newline else ""
        print(newline_res + response)

        response = f'{self.getDateTime()} {response}'
        print(newline_res + response, file=self.log)

        self.log.flush()


    def random_id(self):
        return random.randint(0, 99999999)


    def ischecktype(self, checklist, checktype):
        for i in checklist:
            if isinstance(checktype, list) and type(i) in checktype:
                return True
                
            elif isinstance(checktype, type) and isinstance(i, checktype): 
                return True
            
        return False


    def getDate(self, time = datetime.now()):
        return f'{"%02d" % time.day}.{"%02d" % time.month}.{time.year}'
    
    
    def getTime(self, time = datetime.now()):
        return f'{"%02d" % time.hour}:{"%02d" % time.minute}:{"%02d" % time.second}'


    def getDateTime(self, time = datetime.now()):
        return self.getDate(time) + ' ' + self.getTime(time)


    def makepages(self, obj:list, page_lenght: int = 5, listitem: bool = False):
        listitem_symb = self.getValue("LISTITEM") if listitem else str()
        return Pages(obj, page_lenght, listitem_symb)


    def setValue(self, nameOfObject: str, newValue, exp_type = "package_expr"):
        setExpression(nameOfObject, newValue, exp_type)
        self.update_list(nameOfObject)


    def getValue(self, nameOfObject: str):
        try:
            return getattr(expressions, nameOfObject)
            
        except AttributeError as e:
            return "AttributeError"


    def update_list(self, nameOfObject = ""):
        if hasattr(self, "expression_list"):
            if expressions.list != self.expression_list:
                self.expression_list = expressions.list
                if nameOfObject != "":
                    expressions.parse(nameOfObject)
        
        else:
            self.expression_list = expressions.list



    def add(self, db_name):
        self.__db.add((db_name, self.assets.path + db_name))


    async def getMention(self, page_id: int, name_case = "nom"):
        if name_case == 'link':
            if page_id > 0:
                return f'[id{page_id}|@id{page_id}]'

            elif page_id == self.group_id:
                return self.group_mention

            else:
                test = await self.api.groups.getById(group_id = -page_id)
                return f'[club{-page_id}|@{test[0].screen_name}]'
        
        else:
            if page_id > 0:
                request = await self.api.users.get(
                    user_ids = page_id, 
                    name_case = name_case
                    )
                first_name = request[0].first_name
                
                return f'[id{page_id}|{first_name}]'
            
            elif page_id == self.group_id:
                return self.selfmention[name_case]
            
            else:
                request = await self.api.groups.getById(
                    group_id = -page_id
                    )
                name = request[0].name
                
                return f'[club{-page_id}|{name}]' 


    async def getManagers(self, group_id = None):
        if not group_id:
            group_id = self.group_id

        elif not isinstance(group_id, int):
            raise TypeError('Group ID should be integer')

        lis = await self.api.groups.getMembers(group_id = group_id, sort = 'id_asc', filter='managers')
        return [i.id for i in lis.items if i.role in ['administrator', 'creator', 'moderator']]


    async def isManager(self, from_id: int, group_id = None):
        if not group_id:
            group_id = self.group_id
            
        elif not isinstance(group_id, int):
            raise TypeError('Group ID should be integer')

        return from_id in await self.getManagers(group_id)


    async def getChatManagers(self, peer_id: int):
        res = await self.api.messages.getConversationsById(peer_ids = peer_id)
        res = res.items[0].chat_settings
        response = [*res.admin_ids, res.owner_id]
        return response
        

    def isChatManager(self, from_id, peer_id: int):
        return from_id in self.getChatManagers(peer_id)


    async def getMembers(self, peer_id: int):
        response = await self.api.messages.getConversationMembers(peer_id = peer_id)
        return [i['member_id'] for i in response['items']]


    async def isMember(self, from_id: int, peer_id: int):
        return from_id in await self.getMembers(peer_id)


    def parse_mention(self, mention):
        page_id, call = mention[0: mention.find('|')], mention[mention.find('|') + 1:]

        page_id = page_id.replace('id', '')
        page_id = page_id.replace('club', '-')
        page_id = page_id.replace('public', '-')
            
        return objects.mention(int(page_id), call)


    def parse_link(self, link):
        response = link

        response.replace('https://', '')
        response.replace('http://', '')
        
        return response


class api:
    __slots__ = ('http', '_method', '_string')

    def __init__(self, http, method, string = None):
        self.http = http
        self._method = method    
        self._string = string


    def __getattr__(self, method):
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])

        self._string = self._string + "." if self._string else ""

        return api(
            self.http, self._method,
            (self._string if self._method else '') + method
        )

    async def __call__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)

        result = await self._method(self._string, kwargs)
        if isinstance(result, list):
            return [
                objects.Object(**i) for i in result
            ]
        
        elif isinstance(result, dict):
            return objects.Object(**result)

        else:
            return result


def init_async(coro: asyncio.coroutine, loop = asyncio.get_event_loop()):
    if loop.is_running():
        raise exceptions.LoopStateError("This event loop is currently running")

    else:
        return loop.run_until_complete(coro)
