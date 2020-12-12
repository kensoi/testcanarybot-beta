from .events import events
from .expressions import expression
from .versions_list import static


class mention:
    __slots__ = ('id') 
    def __init__(self, page_id):
        self.id = page_id

    def __int__(self):
        return self.id    
    

class Object:
    def __init__(self, **entries):
        self.__dict__.update(entries)

        for i in self.__dict__.keys():
            setattr(self, i, self.__convert(getattr(self, i)))
            

    def __convert(self, attr):
        attr_type = type(attr)

        if attr_type == dict:
            return key(**attr)

        elif attr_type == list:
            return [self.__convert(i) for i in attr]
        
        else:
            return attr


class key(Object):
    pass


class message(Object):
    id = 0
    date = 0
    random_id = 0
    peer_id = 1
    from_id = 1
    items = []
    type = events.message_new


class package(message):
    pass


class libraryModule:
    codename = "testcanarybot_module"
    name = "testcanarybot sample module"
    version = static
    description = "http://kensoi.github.io/testcanarybot/createmodule.html"
    packagetype = []
