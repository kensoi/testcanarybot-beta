from .versions_list import supporting
class cover_expressions:
    list = []
    types = {
        'log': [],
        'package_expr': [],
        'message_cover': [],
        'workspace': [],
        'bool': [],
        'hidden': []
    }

    def __getattr__(self, name:str):
        return expression(f'UNKNOWN ({name.upper()})', "hidden")

    def parse(self, name):
        pass


class expression:
    __slots__ = ('value', 'type') 
    def __init__(self, variable, exp_type):
        self.value = variable
        self.type = exp_type

    def __str__(self):
        return self.value


class Pages:
    def __init__(self, obj:list, page_lenght: int = 5, listitem: str = ""):
        self.listitem = listitem
        self.source = obj
        self.lenght = len(obj)
        self.page_lenght = page_lenght

        self.pages_count, mod = divmod(self.lenght, self.page_lenght)
        self.pages_count += 1 if mod > 0 else 0


    def get_page(self, page: int):
        if page > self.pages_count or page < 0: raise ValueError("Incorrect page number")

        page_result = self.source[
            page * self.page_lenght:min(self.lenght, (page + 1) * self.page_lenght)
            ]
        
        if self.listitem != str():
            page_result = [f"{self.listitem} {str(i)}" for i in page_result]

        return "\n".join(page_result)

        


def setExpression(name, value: str = "", exp_type = "package_expr"):
    global expressions
    if value == "": value = f":::{name}:::"

    if name in expressions.list:
        if name not in expressions.types['hidden']: 
            getattr(expressions, name).value = value

        else:
            raise TypeError("Incorrect expression")

    else:
        if exp_type in expressions.types.keys():
            expressions.types[exp_type].append(name)
            setattr(expressions, name, expression(value, exp_type))
            expressions.list.append(name)

        else:
            raise TypeError("Incorrect exp_type")


expressions = cover_expressions()

setExpression("LOGGER_START", [f'TESTCANARYBOT {supporting[-1]}', 'KENSOI.GITHUB.IO 2020', ''], "log")
setExpression("SESSION_START", "started", "log")
setExpression("SESSION_LONGPOLL_ERROR", "have not been connected", "log")
setExpression("SESSION_LIBRARY_ERROR", "library directory is broken", "log")
setExpression("SESSION_CLOSE", "session closed", "log")
setExpression("SESSION_START_POLLING", "polling is started \n", "log")
setExpression("SESSION_CLOSE_POLLING", "polling is finished", "log")

setExpression("MESSAGE_HANDLER_ITEMS", "\t\titems: {items}", "log")
setExpression("MESSAGE_HANDLER_TYPE", "{event_type}", "log")
setExpression("MESSAGE_HANDLER_CHAT", "\t\tpeer id: {peer_id}", "log")
setExpression("MESSAGE_HANDLER_USER", "\t\tfrom id: {from_id}", "log")
setExpression("MESSAGE_HANDLER_IT", "\t\ttext: {text}", "log")

setExpression("ENDLINE", exp_type = "workspace")

setExpression("MENTION", exp_type = "workspace")
setExpression("ACTION", exp_type = "workspace")
setExpression("PAYLOAD", exp_type = "workspace")
setExpression("ATTACHMENTS", exp_type = "workspace")

setExpression("NOREACT", exp_type = "workspace")
setExpression("PARSER", exp_type = "workspace")
setExpression("LIBRARY", exp_type = "workspace")
setExpression("LIBRARY_ERROR", exp_type = "workspace")
setExpression("LIBRARY_NOSELECT", exp_type = "workspace")
setExpression("LIBRARY_RELOAD", exp_type = "workspace")
setExpression("LIBRARY_SUCCESS", exp_type = "workspace")

setExpression("LIBRARY_RESPONSE_ERROR", exp_type = "message_cover")
setExpression("LIBRARY_RESPONSE_LIST", exp_type = "message_cover")
setExpression("LIBRARY_RESPONSE_LIST_LINE", "{listitem} {codename} - {name}", "message_cover")
setExpression("LISTITEM", "\u2022", exp_type = "package_expr")
setExpression("LIBRARY_RESPONSE_DESCR", "{name}: \n{descr} ")

setExpression("BEEPA_PAPASA", ":::NYASHKA:NYASHKA:::", "hidden")

setExpression("LIBRARY_UPLOADER_GET", "library directory is listed", "log")
setExpression("MODULE_INIT", "{module} is loaded", "log")
setExpression("MODULE_FAILED_BROKEN", "{module} is broken: no 'Main' class", "log")
setExpression("MODULE_FAILED_SUBCLASS", "{module} is broken: is not inherited from testcanarybot.objects.libraryModule", "log")
setExpression("MODULE_FAILED_PACKAGETYPE", "{module} is broken: module has \"package_handler\" coroutine, but does not have attribute \"packagetype\"", "log")
setExpression("MODULE_FAILED_HANDLERS", """{module} is broken: no any handlers at module. You can put one of these functions:
\t\tasync def error_handler(self, tools, package)
\t\tasync def package_handler(self, tools, package)""", "log")

setExpression("MENTIONS", list(), "workspace")
setExpression("MENTION_NAME_CASES", list(), "workspace")
setExpression("NOT_COMMAND", exp_type = "package_expr")


setExpression("ONLY_COMMANDS", True, "bool")
setExpression("ADD_MENTIONS", False, "bool")

class _ohr:
    from_id = ['deleter_id', 'liker_id', 'user_id']
    peer_id = ['market_owner_id', 'owner_id', 'object_owner_id', 
                'post_owner_id', 'photo_owner_id', 'topic_owner_id', 
                'video_owner_id', 'to_id'
                ]
