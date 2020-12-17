from .versions_list import supporting
from .library import api
from .library import handler
from .library import init_async
from .library import library
from . import exceptions

import aiohttp
import asyncio
import atexit
import os
import time


class multiloop_session:
    """
    wrapper over about aiohttp.request() to avoid errors about loops in threads
    headers: dict()
    """
    methods = ['post', 'get', 'put', 'delete', 'head']

    def __init__(self, headers = None):
        self.headers = headers

    
    def available_methods(self):
        return self.methods


    def __getattr__(self, name):
        if name in self.methods:
            async def request(*args, **kwargs):
                if self.headers:
                    if 'headers' in kwargs:
                        h = kwargs.pop('headers')
                        h.update(self.headers)

                    else:
                        h = self.headers
                        
                elif 'headers' in kwargs:
                    h = kwargs.pop('headers')

                else:
                    h = {}

                async with aiohttp.request(name.upper(), *args, **kwargs, headers = h) as resp:
                    await resp.json()
                    return resp

            return request  

        else:
            AttributeError(f"{name} not found")


class app:  
    headers = {
        'User-agent': """Mozilla/5.0 (Windows NT 6.1; rv:52.0) 
            Gecko/20100101 Firefox/52.0"""
    }

    core_count = 5
    RPS_DELAY = 1 / 20  
    last_request = 0.0
    __handlerlists = []
    __url = ":::"
    __ts = None
    __key = None

    def __init__(self, token: str, group_id: int, api_version='5.126', session = multiloop_session()):
        """
        token: str - token you took from VK Settings: https://vk.com/{yourgroupaddress}?act=tokens
        group_id: int - identificator of your group where you want to install tcb project
        api_version: str - VK API version
        """
        self.http = session(headers = headers)
        
        for filename in ['assets', 'library']:
            if filename in os.listdir(os.getcwd()): continue
            os.mkdir(os.getcwd() + '\\' + filename)
            

        self.__token = token
        self.__group_id = group_id
        self.__av = api_version

        self.api = api(self.http, self.method)
        self.__library = library(supporting, group_id, self.api, self.http)
        
        atexit.register(self.__close)

        text = self.__library.tools.getValue('SESSION_START').value
        print(f"\n@{self.__library.tools.group_address}: {text}\n")
        print(f"\n{self.__library.tools.getDateTime()} @{self.__library.tools.group_address}: {text}\n", file=self.__library.tools.log)


    def __close(self):
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_CLOSE").value, module = "http")
        if not self.__library.tools.log.closed:
            self.__library.tools.log.close()
        

    async def method(self, method: str, values=None):
        """ 
        Init API method

        method: str - method name
        values: dict - parameters.
        """
        data = values if values else dict()
        delay = self.RPS_DELAY - (time.time() - self.last_request)

        if 'group_id' in data: data['group_id'] = self.__group_id
        data['v'] = self.__av
        data['access_token'] = self.__token


        if delay > 0: await asyncio.sleep(delay)

        response = await self.http.post('https://api.vk.com/method/' + method, data = data)
        response = await response.json()

        self.last_request = time.time()
        if 'error' in response: 
            raise exceptions.MethodError(f"[{response['error']['error_code']}] {response['error']['error_msg']}")

        return response['response']    


    def setMentions(self, *args):
        """
        Setup custom mentions instead "@{groupadress}"
        """
        self.__library.tools.setValue("MENTIONS", [self.__library.tools.group_mention, *[str(i).lower() for i in args]])


    def setNameCases(self, *args):
        """
        Setup custom mentions instead \"@{groupaddress}\" for :::MENTION::: syntax
        """
        self.__library.tools.setValue("MENTION_NAME_CASES", args)


    def getModule(self, name: str):
        """
        Get module from your library by name
        name: str - name of library module
        """
        return self.__library.modules[name]


    def hide(self, *args):
        """
        Hide this list of modules.
        """
        self.__library.hidden_modules = args


    def getTools(self):
        """
        Get Tools package to use testcanarybot methods.
        """
        return self.__library.tools


    def getValue(self, string: str):
        """
        Get an expression from list
        """  
        self.__library.tools.getValue(string)
    

    def setValue(self, string: str, value, exp_type = ""):
        """
        Change a value of expression from list
        """  
        self.__library.tools.setValue(string, value, exp_type)


    def setup(self):  
        """
        Manually starting some components that need to work with longpoll. Not necessary to use
        """  
          
        self.__library.upload()
        self.modules_list = list(self.__library.modules.keys())
        init_async(self.__update_longpoll_server(True))

        if len(self.__library.package_handlers) == 0: 
            raise exceptions.LibraryError(
                self.__library.tools.getValue("SESSION_LIBRARY_ERROR"))

        self.__library.tools.update_list()

        for i in range(self.core_count):
            thread = handler(self.__library, i)
            thread.start()
            self.__handlerlists.append(thread)
    

    def start_polling(self):
        """
        Start listenning to VK Longpoll server to get and parse events from it
        """

        self.setup()
        self.__library.tools.system_message(
            self.__library.tools.getValue("SESSION_START_POLLING").value, module = 'longpoll', newline=True)
        asyncio.get_event_loop().run_until_complete(
            self.__pollingCycle())


    def check_server(self, times:int = 1):
        """
        Check VK server to get events and send them to your library to parse once.
        times : int - how many times you need to check.
        """

        self.setup()
        self.__library.tools.system_message(
            self.__library.tools.getValue("SESSION_CHECK_SERVER").value, module = 'longpoll', newline=True)
        
        while times != 0:
            times -= 1
            init_async(self.__polling(), loop=main_loop)
        
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_LISTEN_CLOSE").value, module = 'longpoll')


    async def __update_longpoll_server(self, update_ts=True):
        response = await self.method('groups.getLongPollServer', {'group_id': self.__group_id})

        if update_ts: self.__ts = response['ts']
        self.__key, self.__url = response['key'], response['server']


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
        response = await response.json()

        if 'failed' not in response:
            self.__ts = response['ts']
            return response['updates']

        elif response['failed'] == 1:
            self.__ts = response['ts']

        elif response['failed'] == 2:
            await self.__update_longpoll_server(update_ts=False)

        elif response['failed'] == 3:
            await self.__update_longpoll_server()

        return []


    async def __pollingCycle(self):
        while True: await self.__polling()


    async def __polling(self):
        for event in await self.__check(): 
            for thread in self.__handlerlists:
                if thread.processing: continue
                thread.event = event
                break


    def test_parse(self, event):
        """
        Init test parsing with received event 
        """
        for thread in self.__threadlists:
            if thread.processing:
                continue
            else:
                thread.event = event
                break


    def test_event(self, **kwargs):
        """
        Create test event package for testcanarybot.app.test_parse(event)
        """
        kwargs = kwargs.copy()
        from .events.events import message_new
        
        if kwargs['type'] == message_new:
            from .objects import message as package

        else:
            from .objects import package
        
        event = package(**kwargs)