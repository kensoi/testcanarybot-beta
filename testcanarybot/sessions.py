import threading
import time
import aiohttp
import asyncio
import requests
from .objects import thread_session

class async_session:
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

                session = aiohttp.ClientSession()
                response = await session.request(name, headers = h, *args, **kwargs)
                
                return await response.json(content_type = None)

            return request  

        else:
            AttributeError(f"{name} not found")


class classic_session:
    def __init__(self, *args, **kwargs):
        self.session = requests.session(*args, **kwargs)

    
    def __getattr__(self, name):
        if name in dir(self.session):
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
                response = self.session.request(name, headers = h, *args, **kwargs)
                
                return response.json()

            return request  

        else:
            AttributeError(f"{name} not found")

