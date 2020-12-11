from enum import Enum
class cover_expressions:
    list = []

    def __getattr__(self, name:str):
        return expression(f'UNKNOWN ({name.upper()})')


class expression:
    __slots__ = ('value') 
    def __init__(self, variable):
        self.value = variable

    def __str__(self):
        return self.value


project_name = "TESTCANARYBOT"

module_cover = """from testcanarybot.objects import libraryModule{package_handler_import}

class Main(libraryModule):
    async def start(self, tools):
        self.name = "{name}" # optional
        self.version = 0.851 # optional
        self.description = \"\"\"
            {descr}\"\"\" # optional{package_events}
        
        {package_handler}{error_handler}
"""
package_events = """
        self.packagetype = [
            events.message_new
        ]"""
package_handler = """
    async def package_handler(self, tools, package):
        # tools: testcanarybot.tools
        # package: formatted into message object got from longpoll server
        pass

"""
package_handler_import = ", events # for Main.package_handler"

error_handler = """
    async def error_handler(self, tools, package):
        # tools: testcanarybot.tools
        # package: formatted into message object got from longpoll server
        pass
"""

expressions = cover_expressions()


def setExpression(name, value = None):
    global expressions
    if value == None: value = f":::{name}:::"
        
    setattr(expressions, name, expression(value))
    expressions.list.append(name)


setExpression("LOGGER_START", ['TESTCANARYBOT 0.8', 'KENSOI.GITHUB.IO 2020', ''])
setExpression("SESSION_START", "started")
setExpression("SESSION_LONGPOLL_ERROR", "have not been connected")
setExpression("SESSION_LIBRARY_ERROR", "library directory is broken")
setExpression("SESSION_CLOSE", "session closed")
setExpression("SESSION_START_POLLING", "polling is started")
setExpression("SESSION_CLOSE_POLLING", "polling is finished")

setExpression("MESSAGE_HANDLER_ITEMS", "\t\titems: {items}")
setExpression("MESSAGE_HANDLER_TYPE", "{event_type}")
setExpression("MESSAGE_HANDLER_CHAT", "\t\tpeer id: {peer_id}")
setExpression("MESSAGE_HANDLER_USER", "\t\tfrom id: {from_id}")
setExpression("MESSAGE_HANDLER_IT", "\t\ttext: {text}")

setExpression("ENDLINE")
setExpression("ASSETS_ERROR")

setExpression("MENTION")
setExpression("ACTION")
setExpression("PAYLOAD")
setExpression("ATTACHMENTS")

setExpression("NOREACT")
setExpression("PARSER")
setExpression("LIBRARY")
setExpression("LIBRARY_ERROR")
setExpression("LIBRARY_NOSELECT")
setExpression("LIBRARY_PIC")

setExpression("LIBRARY_RESPONSE_ERROR")
setExpression("LIBRARY_RESPONSE_LIST")
setExpression("LIBRARY_RESPONSE_LIST_LINE", "{listitem} {codename} - {name}")
setExpression("LIBRARY_RESPONSE_LIST_ITEM", "\u2022")
setExpression("LIBRARY_RESPONSE_DESCR", "{name}: \n{descr} ")

setExpression("FWD_MES", "forwarded messages")
setExpression("BEEPA_PAPASA", ":::NYASHKA:NYASHKA:::")

setExpression("LIBRARY_UPLOADER_GET", "library directory is listed")
setExpression("MODULE_INIT", "{module} is loaded")
setExpression("MODULE_FAILED_BROKEN", "{module} is broken: no 'Main' class")
setExpression("MODULE_FAILED_SUBCLASS", "{module} is broken: is not inherited from testcanarybot.objects.libraryModule")
setExpression("MODULE_FAILED_PACKAGETYPE", "{module} is broken: module has \"package_handler\" coroutine, but does not have attribute \"packagetype\"")
setExpression("MODULE_FAILED_HANDLERS", """{module} is broken: no any handlers at module. You can put one of these functions:
\t\tasync def error_handler(self, tools, package)
\t\tasync def package_handler(self, tools, package)""")

setExpression("MENTIONS", list())
setExpression("MENTION_NAME_CASES", list())
setExpression("NOT_COMMAND")


setExpression("ONLY_COMMANDS", True)
setExpression("CHAIN_CM", [])


class events(Enum):
    message_new = 'message_new'
    message_allow = 'message_allow'
    message_deny = 'message_deny'
    message_event = 'message_event'
    
    photo_new = 'photo_new'
    photo_comment_new = 'photo_comment_new'
    photo_comment_edit = 'photo_comment_edit'
    photo_comment_restore = 'photo_comment_restore'
    photo_comment_delete = 'photo_comment_delete'

    audio_new = 'audio_new'

    video_new = 'video_new'
    video_comment_new = 'video_comment_new'
    video_comment_edit = 'video_comment_edit'
    video_comment_restore = 'video_comment_restore'
    video_comment_delete = 'video_comment_delete'

    wall_post_new = 'wall_post_new'
    wall_repost = 'wall_repost'
    wall_reply_new = 'wall_reply_new'
    wall_reply_edit = 'wall_reply_edit'
    wall_reply_restore = 'wall_reply_restore'
    wall_reply_delete = 'wall_reply_delete'

    board_post_new = 'board_post_new'
    board_post_edit = 'board_post_edit'
    board_post_restore = 'board_post_restore'
    board_post_delete = 'board_post_delete'

    market_comment_new = 'market_comment_new'
    market_comment_edit = 'market_comment_edit'
    market_comment_restore = 'market_comment_restore'
    market_comment_delete = 'market_comment_delete'
    market_order_new = 'market_order_new'
    market_order_edit = 'market_order_edit'

    group_leave = 'group_leave'
    group_join = 'group_join'

    user_block = 'user_block'
    user_unblock = 'user_unblock'

    poll_vote_new = 'poll_vote_new'

    group_officers_edit = 'group_officers_edit'
    group_change_settings = 'group_change_settings'
    group_change_photo = 'group_change_photo'

    vkpay_transaction = 'vkpay_transaction'
    app_payload = 'app_payload'

    like_add = 'like_add'
    like_remove = 'like_remove'