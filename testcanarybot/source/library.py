import asyncio
import importlib
import os
import six
import threading
import traceback

from typing import Union
from .events import events
from .versions_list import static

from . import objects
from .expressions import expressions, setExpression, Pages, _ohr

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
        self.daemon = True
        self.handler_id = handler_id

        self.library = library
        self.packages = []


    def run(self):
        self.setName(f"handler_{self.handler_id}")
        self.library.tools.system_message(f"{self.getName()} is started", module = "package_handler")

        self.only_commands = self.library.tools.getValue("ONLY_COMMANDS").value
        self.add_mentions = self.library.tools.getValue("ADD_MENTIONS").value
        self.mentions = self.library.tools.getValue("MENTIONS").value

        self.thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.thread_loop)

        self.thread_loop.run_forever()


    def create_task(self, package):
        if package.type in self.library.event_supports:
            asyncio.run_coroutine_threadsafe(self.resolver(package), self.thread_loop)




    async def resolver(self, package):
        if package.type == events.message_new:
            await asyncio.sleep(0.00001)
            if hasattr(package, 'action'): 
                package.params.action = True

            elif hasattr(package, 'payload'): 
                package.params.payload = True
                package.payload = json.loads(package.params)
            
            elif package.text != '':
                message = package.text.split()
                message[0] = message[0][:-1] if message[0][-1] == ',' else message[0]
                if message[0] in self.mentions:
                    if len(message) > 1:
                        message.pop(0)
                        package.params.command = True
                package = await self.findMentions(package, message)

            elif len(package.attachments) > 0: 
                package.params.attachments = True

            package.params.command = len(package.items) > 0

            if not self.only_commands or package.params.command: 
                await self.handler(package)
            
        else:
            await self.handler(package)


    async def findMentions(self, package, message):
        for count in range(len(message)):
            if message[count][0] == '[' and message[count].count('|') == 1:
                if message[count].count(']') > 0:
                    mention = self.library.tools.parse_mention(
                            message[count][message[count].rfind('[') + 1:message[count].find(']')]
                            )
                    package.params.mentions.append(mention)
                    package.items.append(
                        mention
                        )
                else:
                    for j in range(count, message_lenght):
                        if message[j].count(']') > 0:
                            last_string, message[j] = message[j][0:message[j].find(']')], message[j][message[j].find(']') + 1:]
                            mention = self.library.tools.parse_mention(" ".join([*message[count:j], last_string])[1:])
                            package.items.append(mention)
                            package.params.mentions.append(mention)
                            response.append(message[j])
                            count = j
                            break
            else:
                package.items.append(message[count])
            count += 1
        return package
            

    async def handler(self, package):
        package.items.append(self.library.tools.getValue("ENDLINE"))
        
        for i in self.library.event_supports[package.type]:
            task = self.thread_loop.create_task(
                self.library.modules[i].package_handler(self.library.tools, package)
            )
            await asyncio.sleep(0.00001)



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
                    self.__dbs[name[0]] = objects.database(name[1])

        elif check == tuple:
            if self.check(names[0]):
                raise DBError("This DB already exists")

            else:
                self.__dbs[names[0]] = objects.database(names[1])

        elif check == str:
            if self.check(names):
                raise DBError("This DB already exists")

            else:
                self.__dbs[names] = objects.database(names)
        
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


class tools(objects.tools):
    __module = "system_message"
    log = _assets()("log.txt", "a+", encoding="utf-8")
    __db = databases(("system", "system.db"))

    def __init__(self, number, api, http):
        self.group_id = number
        self.api = api
        self.http = http
        self._ohr = _ohr
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

    async def __call__(self, **kwargs) -> Union[objects.Object, dict]:
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
