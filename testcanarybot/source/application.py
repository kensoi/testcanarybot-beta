from .thread_parser import event_parser
from .versions_list import supporting
from .library import library, api, init_async
from . import exceptions

import aiohttp
import asyncio
import atexit
import os
import time


class multiloop_session:
    """
    wrapper over about aiohttp.request() to avoid errors about loops in threads
    """
    methods = ['post', 'get', 'put', 'delete', 'head']
    def __init__(self, headers = None):
        self.headers = headers


    def __getattr__(self, name):
        if name in self.methods:
            async def request(*args, **kwargs):
                if self.headers:
                    if 'headers' in kwargs:
                        h = kwargs.pop('headers')
                        h.update(self.headers)

                    else:
                        h = self.headers
                else:
                    h = {}

                async with aiohttp.request(name.upper(), *args, **kwargs, headers = h) as resp:
                    await resp.json()
                    return resp

            return request  

        else:
            AttributeError(f"{name} not found")


class app:  
    RPS_DELAY = 1 / 20  
    last_request = 0.0
    headers = dict()
    headers['User-agent'] = """Mozilla/5.0 (Windows NT 6.1; rv:52.0) 
                                Gecko/20100101 Firefox/52.0"""
    http = multiloop_session(headers)

    __ts = None
    __key = None
    
    timeout = aiohttp.ClientTimeout(35)

    def __init__(self, token: str, group_id: int, api_version='5.126'):
        """
        token = token you took from VK Settings: https://vk.com/{yourgroupaddress}?act=tokens
        group_id = identificator of your group where you want to install CanaryBot Framework :)
        """
        
        for filename in ['assets', 'library']:
            if filename in os.listdir(os.getcwd()):
                continue
            
            os.mkdir(os.getcwd() + '\\' + filename)
            

        self.__token = token
        self.__group_id = group_id
        self.api_version = api_version

        self.api = api(self.http, self.method)
        self.__library = library(supporting, group_id, self.api, self.http)
        
        init_async(self.__update_longpoll_server(update_ts=True))
        
        atexit.register(self.__close)

        text = self.__library.tools.getValue('SESSION_START').value
        print(f"\n@{self.__library.tools.group_address}: {text}")
        print(f"\n{self.__library.tools.getDateTime()} @{self.__library.tools.group_address}: {text}", file=self.__library.tools.log)


    def __close(self):
        self.__library.tools.module = "http"
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_CLOSE").value)
        if not self.__library.tools.log.closed:
            self.__library.tools.log.close()
        

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

        delay = self.RPS_DELAY - (time.time() - self.last_request)

        if delay > 0:
            await asyncio.sleep(delay)

        response = await self.http.post(
            'https://api.vk.com/method/' + method, 
            data = data, 
            headers = self.headers
        )
        response = await response.json()

        self.last_request = time.time()
        if 'error' in response:
            raise exceptions.MethodError(f"[{response['error']['error_code']}] {response['error']['error_msg']}")

        return response['response']    


    def setMentions(self, *args):
        """
        Use custom mentions instead "@{groupadress}"
        """
        self.__library.tools.setValue("MENTIONS", [self.__library.tools.group_mention, *[str(i).lower() for i in args]])


    def setNameCases(self, *args):
        """Use custom mentions instead \"@{groupaddress}\""""
        self.__library.tools.setValue("MENTION_NAME_CASES", args)


    def getModule(self, name: str):
        """
        Get module
        """
        return self.__library.modules[name]


    def hide(self, *args):
        """
        Hide this list of modules.
        """
        self.__library.hidden_modules = args


    def getTools(self):
        return self.__library.tools


    def getValue(self, string: str):
        self.__library.tools.getValue(string)
    

    def setValue(self, string: str, value, exp_type = ""):
        self.__library.tools.setValue(string, value, exp_type)


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
    

    def start_polling(self):
        # beta func
        """
        Начать поллинг сервера ВКонтакте на наличие уведомлений.
        """

        self.setup()
        self.__library.tools.module = 'longpoll'
        self.__library.tools.system_message(
            self.__library.tools.getValue("SESSION_START_POLLING").value)
        asyncio.get_event_loop().run_until_complete(
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
            init_async(self.__polling(), loop=main_loop)
        
        self.__library.tools.system_message(self.__library.tools.getValue("SESSION_LISTEN_CLOSE").value)


    async def __update_longpoll_server(self, update_ts=True):
        response = await self.method('groups.getLongPollServer', {'group_id': self.__group_id})

        self.__key = response['key']
        self.__url = response['server']

        if update_ts: self.__ts = response['ts']


    async def __check(self):
        values = {
            'act': 'a_check',
            'key': self.__key,
            'ts': self.__ts,
            'wait': 25,
        }
        response = await self.http.get(
            self.__url,
            params = values,
            timeout = self.timeout
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
        # beta coro

        while True:
            await self.__polling()


    async def __polling(self):
        # beta coro

        eventslist = await self.__check()

        for event in eventslist:
            my_thread = event_parser(self.__library, event)
            my_thread.start()


    def test_run(self, event):
        #beta func
        """
        Run test for library.
        """
        my_thread = event_parser(self.__library, event)
        my_thread.start()


    def create_testevent(self, *args, **kwargs):
        kwargs = kwargs.copy()
        from .events.events import message_new
        
        if kwargs['type'] == message_new:
            from .objects import message as package

        else:
            from .objects import package
        
        event = package(**kwargs)