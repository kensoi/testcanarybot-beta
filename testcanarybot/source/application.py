from .versions_list import supporting
from .library import api
from .library import handler
from .library import init_async
from .library import library
from . import exceptions

from .objects import multiloop_session, package, Object
from .events import events
import asyncio
import atexit
import os
import time


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
    __debug = False
    __lastthread = 0

    def __init__(self, access_token: str, group_id: int, api_version='5.126', service_token: str = "", core_count = 5, session = multiloop_session):
        """
        token: str - token you took from VK Settings: https://vk.com/{yourgroupaddress}?act=tokens
        group_id: int - identificator of your group where you want to install tcb project
        api_version: str - VK API version
        """
        self.http = session(headers = self.headers)
        
        for filename in ['assets', 'library']:
            if filename in os.listdir(os.getcwd()): continue
            os.mkdir(os.getcwd() + '\\' + filename)
            

        self.__token = access_token
        self.__loop = asyncio.get_event_loop()
        self.__service = service_token
        self.__group_id = group_id
        self.__av = api_version
        self.core_count = core_count

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
        self.__debug = self.getTools().getValue("DEBUG_MESSAGES")

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
        self.__loop.run_until_complete(
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
        if self.__debug:
            self.getTools().system_message( 
                module="longpoll",
                textToPrint = "Longpoll server updated"
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
            self.__loop.create_task(self.__parse(event))
    
    
    async def __parse(self, event, thread = None):
        thread = self.getThread()

        if event['type'] == 'message_new':
            package_res = package(**event['object']['message'])
            package_res.params.client_info = Object(**event['object']['client_info'])
            package_res.params.from_chat = package_res.peer_id > 2000000000


        else:
            package_res = package(**event['object'])

            for key, value in event['object'].items():
                if key in self.getTools()._ohr.peer_id: package_res.peer_id = value
                if key in self.getTools()._ohr.from_id: package_res.from_id = value

        package_res.event_id = event['event_id']
        package_res.type = getattr(events, event['type'])
        package_res.items = []
        
        self.getThread().create_task(package_res)

        
    def getThread(self):
        self.__lastthread +=1 
        if self.__lastthread == len(self.__handlerlists): self.__lastthread = 0
        return self.__handlerlists[self.__lastthread]


    def test_parse(self, event: package):
        """
        Init test parsing with received event 
        """
        self.getThread().create_task(event)



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