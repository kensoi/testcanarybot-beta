import six
import typing
from . import objects

class api:
    __slots__ = ('http', '_method', '_string')

    def __init__(self, http, method = None, string = None):
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

    async def __call__(self, **kwargs) -> typing.Union[objects.data, dict]:
        for k, v in six.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)

        result = await self._method(self._string, kwargs)
        if isinstance(result, list):
            return [
                objects.data(**i) for i in result
            ]
        
        elif isinstance(result, dict):
            return objects.data(**result)

        else:
            return result