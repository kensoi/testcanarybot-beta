from . import exceptions
from . import objects
from ._values import events
from ._values import expressions
from ._values import setExpression
from .tools import assets

from datetime import datetime

import aiohttp
import atexit
import asyncio
import importlib
import json
import os
import random
import sqlite3
import threading
import time
import traceback
import six

main_loop = asyncio.get_event_loop()

def init_async(coroutine: asyncio.coroutine, loop = None):
    if not loop: loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

class event_parser(threading.Thread):
    def __init__(self, library, event):
        threading.Thread.__init__(self)

        self.thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.thread_loop)

        self.library = library
        self.event = event


    def run(self):
        if isinstance(self.event, dict):
            if hasattr(events, self.event['type']):
                event_type = getattr(events, self.event['type'])

                if event_type == events.message_new:
                    package = objects.message(**self.event['object']['message'])
                    package.items = []

                    if hasattr(package, 'action'): 
                        package.items = [self.library.tools.getValue("ACTION")]
                    
                    elif hasattr(package, 'payload'):
                        package.items.append(self.library.tools.getValue("PAYLOAD"))
                        package.payload = json.loads(package.payload)

                    elif package.text != '': 
                        package.items = self.parse_command(package.text)

                    elif len(package.attachments) > 0: 
                        package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                        
                    package.items.append(self.library.tools.getValue("ENDLINE"))
                    if len(package.items) != 0 or not self.library.tools.getValue("ONLY_COMMANDS").value:
                        self.parse_package(package)

                else:
                    package = objects.package(**dict())
                    event_object = self.event['object']
                    package.peer_id = event_object['user_id']

                    for key, value in obj.items():
                        if key in _ohr.peer_id: 
                            package.peer_id = value

                        if key in _ohr.from_id: 
                            package.from_id = value

                        package[key] = value
                    
                    package.items.append(self.event)
                    package.items.append(self.library.tools.getObject("ENDLINE"))
                    package.type = event_type
                    package.__dict__.update(
                        event_object
                    )

                    self.parse_package(package)
                    
        elif issubclass(type(self.event), objects.Object):
            package = self.event
            package.type = events.message_new
            package.items = []

            if hasattr(package, 'action'): 
                package.items = [self.library.tools.getValue("ACTION")]
            
            elif hasattr(package, 'payload'):
                package.items.append(self.library.tools.getValue("PAYLOAD"))
                package.payload = json.loads(package.payload)

            elif package.text != '': 
                package.items = self.parse_command(package.text)

            elif len(package.attachments) > 0: 
                package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                
            package.items.append(self.library.tools.getValue("ENDLINE"))
            if len(package.items) != 0 or not self.library.tools.getValue("ONLY_COMMANDS").value:
                self.parse_package(package)
        


    def parse_command(self, messagetoreact):
        for i in self.library.tools.expression_list:
            value = self.library.tools.getValue(i)

            if type(value) is str and value in messagetoreact:
                messagetoreact = messagetoreact.replace(i, ':::SYSTEM:::')

        response = []
        message = messagetoreact.split() 

        if len(message) > 1:
            if message[0] in [*self.library.tools.getValue("MENTIONS").value]:
                message.pop(0)

                for i in message:
                    if i[0] == '[' and i[-1] == ']' and i.count('|') == 1:
                        response.append(self.library.tools.parse_mention(i[1:-1]))

                    else:
                        response.append(self.library.tools.parse_link(i))

            if len(response) != 0:
                return response
        
        if self.library.tools.getValue("ADD_MENTIONS").value:
            for word in message:
                if word.lower() in [*self.library.tools.getValue("MENTIONS").value, 
                                    *self.library.tools.getValue("MENTION_NAME_CASES").value]: 
                    response.append(self.library.tools.getValue("MENTION"))

            if len(response) != 0:
                return response

        if not self.library.tools.getValue("ONLY_COMMANDS").value:
            response.append(self.library.tools.getValue("NOT_COMMAND"))
            return response

        return []


    def parse_package(self, event_package):
        if (not self.library.tools.getValue("ONLY_COMMANDS")) == (len(event_package.items) == 1):
            if event_package.type in self.library.event_supports.keys():
                itemscopy = event_package.items.copy()
                modules = [asyncio.ensure_future(self.library.modules[i].package_handler(self.library.tools, event_package), loop = self.thread_loop) for i in self.library.event_supports[event_package.type]]
                        
                self.library.tools.module = 'message_handler'
                
                reaction = self.thread_loop.run_until_complete(
                    asyncio.gather(*modules)
                    )

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
                response += self.library.tools.getValue("MESSAGE_HANDLER_ITEMS").value + '\n'
                if hasattr(event_package, 'text'): response += self.library.tools.getValue("MESSAGE_HANDLER_IT").value + '\n'
                
                response = response.format(
                    peer_id = event_package.peer_id,
                    from_id = event_package.from_id,
                    event_type = event_package.type.value,
                    items = itemscopy[:-1],
                    text = event_package.text
                )
                self.library.tools.system_message(response)


class _ohr:
    from_id = ['deleter_id', 'liker_id', 'user_id']
    peer_id = ['market_owner_id', 'owner_id', 'object_owner_id', 
                'post_owner_id', 'photo_owner_id', 'topic_owner_id', 
                'video_owner_id', 'to_id'
                ]


class api:
    __slots__ = ('_http', '_method', '_string')

    def __init__(self, __http, method, string = None):
        self._http = __http
        self._method = method    
        self._string = string


    def __getattr__(self, method):
        if '_' in method:
            m = method.split('_')
            method = m[0] + ''.join(i.title() for i in m[1:])

        self._string = self._string + "." if self._string else ""

        return api(
            self._http, self._method,
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


class app:    
    __RPS_DELAY = 1 / 20.0
    headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) '
                            'Gecko/20100101 Firefox/52.0'
        }

    def __init__(self, token: str, group_id: int, api_version='5.126'):
        """
        Token = token you took from VK Settings: https://vk.com/{yourgroupaddress}?act=tokens
        group_id = identificator of your group where you want to install CanaryBot Framework :)
        """
        
        for filename in ['\\assets\\', '\\library\\']:
            try:
                os.mkdir(os.getcwd() + filename)
            except:
                pass
        
        self.last_request = 0.0

        self.__token = token
        self.__group_id = group_id
        self.api_version = api_version

        self.longpoll = None
        self.__http = session_async(self.headers)
        self.api = api(self.__http, self.method)
        self.__library = library(supporting, group_id, self.api, self.__http)
        
        
        self.atexit = atexit
        self.atexit.register(self.__close_session)

        text = self.__library.tools.getValue('SESSION_START').value
        print(f"\n@{self.__library.tools.group_address}: {text}")
        print(f"\n{self.__library.tools.getDateTime()} @{self.__library.tools.group_address}: {text}", file=self.__library.tools.log)


    def __close_session(self):
        main_loop.run_until_complete(self.__http.close())
        self.__library.tools.module = "http"
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_CLOSE").value)
        if not self.__library.tools.log.closed:
            self.__library.tools.log.close()


    async def get(self, *args, **kwargs):
        self.__http.get(*args, **kwargs)


    async def post(self, *args, **kwargs):
        self.__http.post(*args, **kwargs)


    async def method(self, method: str, values=None):
        """ Вызов метода API

        :param method: название метода
        :type method: str

        :param values: параметры
        :type values: dict
        """
        data = values if values else dict()

        data['v'] = self.api_version

        data['access_token'] = self.__token
        if 'group_id' in data: data['group_id'] = self.__group_id

        delay = self.__RPS_DELAY - (time.time() - self.last_request)

        if delay > 0:
            await asyncio.sleep(delay)

        response = await self.__http.post(
            'https://api.vk.com/method/' + method, 
            data = data, 
            headers = self.headers
        )

        self.last_request = time.time()

        response = await response.json()
        if 'error' in response:
            
            raise TypeError(f"[{response['error']['error_code']}] {response['error']['error_msg']}")

        return response['response']    


    def setMentions(self, *args):
        """
        Use custom mentions instead "@{groupadress}"
        """
        self.__library.tools.setValue("MENTIONS", [self.__library.tools.group_mention, *[str(i).lower() for i in args]])


    def setNameCases(self, *args):
        """Use custom mentions instead \"@{groupaddress}\""""
        self.__library.tools.setValue("MENTION_NAME_CASES", args)


    def getTools(self):
        return self.__library.tools


    def getValue(self, string: str):
        self.__library.tools.getValue(string)
    

    def setValue(self, string: str, value):
        self.__library.tools.setValue(string, value)


    def getModule(self, name: str):
        """
        Get module
        """
        return self.__library.modules[name]


    def hide(self, *args):
        """
        Hide this list of modules.
        """
        self.__library.hidden_modules = [*args, 'static']


    def setup(self):  
        # beta func  
        """
        Ручной запуск установки нужных компонентов, необязательно к использованию.
        """  
          
        self.__library.upload()
        self.modules_list = list(self.__library.modules.keys())

        if len(self.__library.package_handlers) == 0: 
            raise exceptions.LibraryError(
                self.__library.tools.getValue("SESSION_LIBRARY_ERROR"))

        self.__library.tools.update_list()
        self.longpoll = longpoll(self.__http, self.method, self.__group_id)
    

    def start_polling(self):
        # beta func
        """
        Начать поллинг сервера ВКонтакте на наличие уведомлений.
        """

        self.setup()
        self.__library.tools.system_message(
            self.__library.tools.getValue("SESSION_START_POLLING").value)
        main_loop.run_until_complete(
            self.__pollingCycle())


    def check_server(self, times = 1):
        # beta func
        """
        Проверить сервер ВКонтакте на наличие уведомлений определённое число раз (times).
        """

        self.setup()
        self.__library.tools.system_message(
            self.__library.tools.getValue("SESSION_CHECK_SERVER").value)
        while times != 0:
            times -= 1
            init_async(self.__polling())
        
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_LISTEN_CLOSE").value)


    async def __pollingCycle(self):
        # beta coro

        while True:
            await self.__polling()


    async def __polling(self):
        # beta coro

        eventslist = await self.longpoll.check()

        for event in eventslist:
            my_thread = event_parser(self.__library, event)
            my_thread.start()


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

    error_handlers = ['static']
    package_handlers = ['static']
    hidden_modules = []


    def __init__(self, v, group_id, api, http):
        self.supp_v = v
        self.tools = tools(group_id, api, http)


    def upload(self):
        if 'library' in os.listdir(os.getcwd()):
            self.tools.module = "library.uploader"
            self.tools.system_message(self.tools.getValue("LIBRARY_UPLOADER_GET"))
            
            main_loop.run_until_complete(asyncio.gather(*[
                                    self.moduleload(module) for module in filter(
                                        lambda module_name: 0 if module_name != '__pycache__' else 1, 
                                        os.listdir(os.getcwd() + '\\library\\'))
                                    ]))
        
        
    async def moduleload(self, module_name):
        module = importlib.import_module("library." + module_name[:-3] if module_name.endswith('.py') else module_name + 'main')
        
        if hasattr(module, 'Main'):
            moduleObj = module.Main()
            if issubclass(type(module), objects.libraryModule):
                await moduleObj.start(self.tools)
            else:
                return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                    module = module_name))


        else:
            return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                module = module_name))

        if hasattr(moduleObj, 'error_handler'): self.error_handlers.append(module_name)
        if hasattr(moduleObj, 'package_handler'):
            if len(moduleObj.packagetype) > 0:
                for package in moduleObj.packagetype.packagetype:
                    if package not in self.__compactible: self.__compactible[package] = list()
                    self.__compactible[package].append(module_name)

                self.package_handlers.append(module_name)

            else:
                return self.tools.system_message(self.tools.getValue("MODULE_FAILED_PACKAGETYPE").value.format(
                    module = module_name))

        if module_name in [*self.error_handlers, *self.package_handlers]:
            self.modules[module_name] = moduleObj
            return self.tools.system_message(self.tools.getValue("MODULE_INIT").value.format(
                module = module_name))

        else:
            return self.tools.system_message(self.tools.getValue("MODULE_FAILED_HANDLERS").value.format(
                module = module_name))


    def getCompactible(self, packagetype):
        for module in self.package_handlers:
            if packagetype in self.modules[module].packagetype: yield module


class longpoll:
    def __init__(self, session, method, group_id):
        self.session = session
        self.method = method
        self.group_id = str(group_id)
        
        self.url = None
        self.key = None
        self.server = None
        self.ts = None

        self.timeout = aiohttp.ClientTimeout(total = 35)

        init_async(self.update_longpoll_server())
        

    async def update_longpoll_server(self, update_ts=True):
        values = {
            'group_id': self.group_id
        }
        response = await self.method('groups.getLongPollServer', values)

        self.key = response['key']
        self.server = response['server']

        self.url = self.server

        if update_ts:
            self.ts = response['ts']


    async def check(self):
        values = {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': 25,
        }

        response = await self.session.get(
            self.url,
            params = values,
            timeout = self.timeout
        )
        response = await response.json()

        if 'failed' not in response:
            self.ts = response['ts']
            return response['updates']

        elif response['failed'] == 1:
            self.ts = response['ts']

        elif response['failed'] == 2:
            await self.update_longpoll_server(update_ts=False)

        elif response['failed'] == 3:
            await self.update_longpoll_server()

        return []


class session_async:
    """
    wrapper over about aiohttp.ClientSession() to avoid RuntimeError/ServerDisconnectedError
    """
    def __init__(self, headers):
        self.__http = None
        self.headers = headers
        self.all_exceptions = [
                "ClientError",
                "ClientConnectionError",
                "ClientOSError",
                "ClientConnectorError",
                "ClientProxyConnectionError",
                "ClientSSLError",
                "ClientConnectorSSLError",
                "ClientConnectorCertificateError",
                "ServerConnectionError",
                "ServerTimeoutError",
                "ServerDisconnectedError",
                "ServerFingerprintMismatch",
                "ClientResponseError",
                "ClientHttpProxyError",
                "WSServerHandshakeError",
                "ContentTypeError",
                "ClientPayloadError",
                "InvalidURL"
        ]
        self.update_ignorelist(
            [
                "ServerDisconnectedError"
                ]
            )

    
    def update_ignorelist(self, ignorelist: list):
        self.ignore_exceptions = [
            getattr(aiohttp.client_exceptions, i) for i in ignorelist
            ]


    async def update_http(self):
        if self.__http:
            await self.__http.close()
            self.__http = None
        self.__http = aiohttp.ClientSession()


    def __getattr__(self, name):
        if name in ['post', 'get']:
            return self.__request_get(name)

        else:
            return getattr(self.__http, name)


    def __request_get(self, name):
        self.last_method = name
        return self.__request


    async def __request(self, *args, **kwargs):
        h = kwargs.pop('headers') if 'headers' in kwargs else self.headers

        if not self.__http:
            await self.update_http()

        try:
            return await getattr(self.__http, self.last_method)(headers = h, *args, **kwargs)

        except (RuntimeError, OSError, *self.ignore_exceptions) as e:
            await self.update_http()
            return await getattr(self.__http, self.last_method)(headers = h, *args, **kwargs)


class tools:
    module = "system"
    __db = databases(("system", "system.db"))
    get = self.__db.get

    log = assets("log.txt", "a+", encoding="utf-8")
    def __init__(self, number, api, http):
        self.group_id = number
        self.api = api
        self.http = http
        init_async(self.__setShort())

        self.group_mention = f'[club{self.group_id}|@{self.group_address}]'
        self.mentions = [self.group_mention]
        self.mentions_name_cases = []


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


    def system_message(self, textToPrint:str):
        response = f'@{self.group_address}.{self.module}: {textToPrint}'

        if self.log.closed:
            self.log = assets("log.txt", "a+", encoding="utf-8")
        
        print(response)
        print(f"{self.getDateTime()} {response}", file=self.log)

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


    def setValue(self, nameOfObject: str, newValue):
        setExpression(nameOfObject, newValue)
        self.update_list()


    def getValue(self, nameOfObject: str):
        try:
            return getattr(expressions, nameOfObject)
            
        except AttributeError as e:
            return "AttributeError"


    def update_list(self):
        if hasattr(self, "expression_list"):
            if expressions.list != self.expression_list:
                self.expression_list = expressions.list
        
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
        return [i.id for i in lis.items if i.role in ['administrator', 'creator']]


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
        response = mention.replace(mention[mention.find('|'):], '')

        response = response.replace('id', '')
        response = response.replace('club', '-')
        response = response.replace('public', '-')
            
        return objects.mention(int(response))


    def parse_link(self, link):
        response = link

        response.replace('https://', '')
        response.replace('http://', '')
        
        return response




supporting = [
    objects.static, *[(0.85 + 0.001) // 0.001 * 0.001 for i in range(1, 2)]
    ]