import asyncio
import aiohttp
import atexit
import os
import threading
import time
import typing

from . import exceptions
from . import objects

from .enums import values
from .enums import events
from .library import api
from .library import handler
from .library import init_async
from .library import library
from .library import assets

from .values import _ohr
from .versions_list import supporting


class async_sessions():
    """
    wrapper over about aiohttp.request() to avoid errors about loops in threads
    headers: dict()
    """

    def __init__(self, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        self.__sessions = {}

        self.create_session(threading.current_thread())


    def create_session(self, thread: threading.Thread) -> None:
        if not hasattr(thread, 'session'): 
            thread.session = aiohttp.ClientSession(*self.__args, **self.__kwargs)


    def __getattr__(self, name):
        if name in dir(aiohttp.ClientSession):
            thread = threading.current_thread()
            self.create_session(thread)
            return getattr(thread.session, name)


class app:  
    headers = {
        'User-agent': """Mozilla/5.0 (Windows NT 6.1; rv:52.0) 
            Gecko/20100101 Firefox/52.0"""
    }

    handlers_count = 5
    RPS_DELAY = 1 / 20  
    last_request = 0.0
    __handlerlists = []
    __url = "$$$"
    __ts = None
    __key = None
    __lastthread = 0

    def __init__(self, access_token: str, group_id: int, api_version: str = '5.126', service_token: typing.Optional[str] = None, handlers_count:int = 5, session = async_sessions):
        """
        access_token [str] - token you took from VK Settings: https://vk.com/{yourgroupaddress}?act=tokens
        group_id [int] - identificator of your group where you want to install tcb project
        api_version: [str] - VK API version (default: 5.126)
        service_token [str] - token of your app for service type of access (paste to your query )
        handlers_count [int] - count of thread handlers you need to create.
        session [object or ClientSession] - change default session (default: testcanarybot.source.application.async_sessions)
        """
        self.http = session(headers = self.headers)
        
        for filename in ['assets', 'library']:
            if filename in os.listdir(os.getcwd()): continue
            os.mkdir(os.getcwd() + '\\' + filename)

        self.log = assets("log.txt", "a+", encoding="utf-8")

        self.__token = access_token
        self.__loop = asyncio.get_event_loop()
        self.__service = service_token
        self.__group_id = group_id
        self.__av = api_version
        self.handlers_count = handlers_count

        self.api = api(self.http, self.method)
        self.__library = library(supporting, group_id, self.api, self.http, self.log)
        
        atexit.register(self.__close)
        self.__library.tools.system_message(
            module = self.http.__class__.__name__, 
            write = str(self.getTools().values.SESSION_START))


    def __close(self):
        self.__library.tools.system_message(module = self.http.__class__.__name__, write = self.getTools().values.SESSION_CLOSE)

        if self.log.closed:
            self.log = assets("log.txt", "a+", encoding="utf-8")

        for print_test in self.getTools().values.LOGGER_CLOSE.value:
            print(print_test, 
                file = self.log
                )

        if not self.log.closed:
            self.log.close()
        

    async def method(self, method: str, values=None):
        """ 
        Init API method

        method [str] - method name
        values [dict] - parameters.
        """
        data = values if values else dict()
        delay = self.RPS_DELAY - (time.time() - self.last_request)

        if 'group_id' in data: data['group_id'] = self.__group_id
        data['v'] = self.__av

        access_type = values.get('type', "bot")

        if access_type in ["bot", "service"]:
            if access_type == "service" and self.__service != "":
                data['access_token'] = self.__service
            else:
                data['access_token'] = self.__token
        else: 
            raise ValueError("Incorrect method type")


        if delay > 0: await asyncio.sleep(delay)

        response = await self.http.post('https://api.vk.com/method/' + method, data = data)
        response = await response.json(content_type = None)

        self.last_request = time.time()
        if 'error' in response: 
            raise exceptions.MethodError(f"[{response['error']['error_code']}] {response['error']['error_msg']}")

        return response['response']    


    def setMentions(self, mentions: list):
        """
        Setup custom mentions instead "@{groupadress}"
        """
        self.__library.tools.values.set("MENTIONS", [self.__library.tools.group_mention, *[str(i).lower() for i in mentions]])


    def getModule(self, name: str) -> objects.libraryModule:
        """
        Get module from your library by name
        name: str - name of library module
        """
        return self.__library.modules[name]


    def getTools(self):
        """
        Get Tools package to use testcanarybot methods.
        """
        return self.__library.tools


    def getValue(self, name: str):
        """
        Get an expression from list
        """  
        return getattr(self.getTools().values, name)
    

    def setValue(self, name: str, value: typing.Any = None, stype: typing.Optional[values] = None):
        """
        Change a value of expression from list
        """
        self.getTools().values.set(name, value = value, stype = stype)


    def setup(self):  
        """
        Manually starting some components that need to work with longpoll. Not necessary to use
        """  
          
        self.__library.upload()
        self.modules_list = list(self.__library.modules.keys())
        init_async(self.__update_longpoll_server(True))

        if len(self.__library.modules.keys()) == 0: 
            raise exceptions.LibraryError(
                self.getTools().values.LIBRARY_ERROR)

        for print_test in self.getTools().values.LOGGER_START.value:
            print(print_test, 
                file = self.log
                )
                

        for i in range(self.handlers_count):
            thread = handler(self.__library, i)
            thread.start()
            self.__handlerlists.append(thread)
    

    def start_polling(self) -> None:
        """
        Start listenning to VK Longpoll server to get and parse events from it
        """

        self.setup()
        self.__library.tools.system_message(
            str(self.getTools().values.LONGPOLL_START), module = 'longpoll', newline=True)
        self.__loop.run_until_complete(
            self.__pollingCycle())


    def check_server(self, times: int = 1) -> None:
        """
        Check VK server to get events and send them to your library to parse once.
        times : int - how many times you need to check.
        """

        self.setup()
        self.__library.tools.system_message(
            module = 'longpoll', newline = True,
            write = str(self.getTools().values.LONGPOLL_CHECK))
        
        while times != 0:
            times -= 1
            init_async(self.__polling())
        
        self.getTools().system_message(module = 'longpoll',
            write = self.getTools().values.LONGPOLL_CLOSE)


    async def __update_longpoll_server(self, update_ts: bool = True) -> None:
        response = await self.method('groups.getLongPollServer', {'group_id': self.__group_id})

        if update_ts: self.__ts = response['ts']
        self.__key, self.__url = response['key'], response['server']

        if self.getTools().values.DEBUG_MESSAGES:
            self.getTools().system_message( 
                module="longpoll",
                write = self.getTools().values.LONGPOLL_UPDATE.value
                )


    async def __check(self):
        values = {
            'act': 'a_check',
            'key': self.__key,
            'ts': self.__ts,
            'wait': 25,
        }
        response = await self.http.get(
            self.__url,
            params = values
        )
        response = await response.json(content_type = None)

        if 'failed' not in response:
            self.__ts = response['ts']
            return response['updates']

        elif response['failed'] == 1:
            self.__ts = response['ts']

        elif response['failed'] == 2:
            await self.__update_longpoll_server(False)

        elif response['failed'] == 3:
            await self.__update_longpoll_server()

        return []


    async def __pollingCycle(self):
        while True: await self.__polling()


    async def __polling(self):
        for event in await self.__check():
            self.__loop.create_task(self.__parse(event))
    
    
    async def __parse(self, event, thread = None):
        if event['type'] == 'message_new':
            package = objects.package(**event['object']['message'])
            package.params.client_info = objects.data(**event['object']['client_info'])
            package.params.from_chat = package.peer_id > 2000000000


        else:
            package = objects.package(**event['object'])

            for key, value in event['object'].items():
                if key in _ohr.peer_id: package.peer_id = value
                if key in _ohr.from_id: package.from_id = value

        package.type = getattr(events, event['type'])
        package.event_id = event['event_id']
        package.items = []
        self.__getThread().create_task(package)

        
    def __getThread(self):
        self.__lastthread = 0 if self.__lastthread + 1 == len(self.__handlerlists) else self.__lastthread + 1
        return self.__handlerlists[self.__lastthread]


    def test_parse(self, event: objects.package):
        """
        Init test parsing with received event 
        """
        self.__getThread().create_task(event)