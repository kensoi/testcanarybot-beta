import asyncio
import importlib
import os
import six
import sqlite3
import random

from . import objects
from datetime import datetime
from .expressions import expressions, setExpression

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


    def upload(self):
        if 'library' in os.listdir(os.getcwd()):
            self.tools.module = "library.uploader"
            self.tools.system_message(self.tools.getValue("LIBRARY_UPLOADER_GET"))
            
            listdir = os.listdir(os.getcwd() + '\\library\\')
            listdir.remove("__pycache__")
            if len(listdir) == 0:
                raise exceptions.LibraryError(
                    self.__library.tools.getValue("SESSION_LIBRARY_ERROR"))
                
            init_async(
                asyncio.wait(
                    [
                        asyncio.get_event_loop().create_task(self.moduleload(module)) for module in listdir
                    ]
                )
            )
            self.tools.system_message(
                "Supporting event types: {event_types}".format(
                    event_types = "\n".join(["", *["\t\t" + str(i) for i in self.event_supports.keys()]])
                )
            )
        
        
    async def moduleload(self, module_name):
        module = importlib.import_module("library." + module_name[:-3] if module_name.endswith('.py') else module_name + 'main')
        if module_name[-3:] == '.py': module_name = module_name[:-3]
        if hasattr(module, 'Main'):
            moduleObj = module.Main()
            if issubclass(type(moduleObj), objects.libraryModule) or self.needattr & set(dir(moduleObj)) == self.needattr:
                if hasattr(moduleObj, "start"):
                    await moduleObj.start(self.tools)

            else:
                return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                    module = module_name))


        else:
            return self.tools.system_message(self.tools.getValue("MODULE_FAILED_BROKEN").value.format(
                module = module_name))

        if hasattr(moduleObj, 'error_handler'): self.error_handlers.append(module_name)
        if hasattr(moduleObj, 'package_handler'):
            if hasattr(moduleObj, 'packagetype') and len(moduleObj.packagetype) > 0:
                for package in moduleObj.packagetype:
                    if package not in self.event_supports: self.event_supports[package] = list()
                    self.event_supports[package].append(module_name)

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
        if packagetype in self.event_supports:
            return self.event_supports[packagetype]
        else:
            return []


class tools:
    module = "system"
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


    def setValue(self, nameOfObject: str, newValue, exp_type = ""):
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
