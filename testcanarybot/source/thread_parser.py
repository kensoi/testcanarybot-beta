import asyncio
import threading
import traceback


from .events import events
from . import objects
from .versions_list import static


class event_core(threading.Thread):
    processing = False

    def __init__(self, library, handler_id):
        threading.Thread.__init__(self)
        self.thread_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.thread_loop)
        self.daemon = True
        self.handler_id = handler_id

        self.library = library
        self.event = None


    def run(self):
        self.setName(f"handler_{self.handler_id}")
        self.library.tools.system_message(f"started ({self.getName()})", module = "message_handler")
        while True:
            if self.event: 
                self.processing = True
                self.parse_event(self.event)
                self.event = None
                self.processing = False


    def parse_event(self, event):
        if isinstance(event, dict):
            if hasattr(events, event['type']):
                event_type = getattr(events, event['type'])

                if event_type == events.message_new:
                    package = objects.message(**event['object']['message'])
                    package.items = []

                    if hasattr(package, 'action'): 
                        package.items.append(self.library.tools.getValue("ACTION"))
                    
                    elif hasattr(package, 'payload'):
                        package.items.append(self.library.tools.getValue("PAYLOAD"))
                        package.payload = json.loads(package.payload)

                    elif package.text != '': 
                        package.items, package.mentions = self.parse_command(package.text)

                    elif len(package.attachments) > 0: 
                        package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                        
                    package.items.append(self.library.tools.getValue("ENDLINE"))
                    if not self.library.tools.getValue("ONLY_COMMANDS").value:
                        self.parse_package(package)

                else:
                    package = objects.package(**event['object'])
                    event_object = event['object']

                    for key, value in event_object.items():
                        if key in _ohr.peer_id: 
                            package.peer_id = value

                        if key in _ohr.from_id: 
                            package.from_id = value

                    package.items.append(self.library.tools.getValue("ENDLINE"))
                    package.type = event_type
                    package.__dict__.update(
                        event_object
                    )

                    self.parse_package(package)  

        elif issubclass(type(self.event), objects.Object):
            package = self.event
            package.items = []
            if package.type == events.message_new:

                if hasattr(package, 'action'): 
                    package.items.append(self.library.tools.getValue("ACTION"))
                
                elif hasattr(package, 'payload'):
                    package.items.append(self.library.tools.getValue("PAYLOAD"))
                    package.payload = json.loads(package.payload)

                elif package.text != '': 
                    package.items, package.mentions = self.parse_command(package.text)

                elif len(package.attachments) > 0: 
                    package.items.append(self.library.tools.getValue("ATTACHMENTS"))
                    
                package.items.append(self.library.tools.getValue("ENDLINE"))
                if not self.library.tools.getValue("ONLY_COMMANDS").value:
                    self.parse_package(package)
            else:
                package.items.append(self.library.tools.getValue("ENDLINE"))
                self.parse_package(package)


    def parse_command(self, messagetoreact):
        response, mentions = [], []
        message = messagetoreact.split() 

        if len(message) > 1:
            if message[0] in [*self.library.tools.getValue("MENTIONS").value]:
                message.pop(0)
                message_lenght = len(message)
                i = 0
                while i != message_lenght:
                    if message[i][0] == '[' and message[i].count('|') == 1:
                        if message[i].count(']') > 0:
                            mention = self.library.tools.parse_mention(
                                    message[i][message[i].rfind('[') + 1:message[i].find(']')]
                                    )
                            mentions.append(mention)
                            response.append(
                                mention
                                )
                        else:
                            for j in range(i, message_lenght):
                                if message[j].count(']') > 0:
                                    last_string, message[j] = message[j][0:message[j].find(']')], message[j][message[j].find(']') + 1:]
                                    mention = " ".join([*message[i:j], last_string])[1:]
                                    mention = self.library.tools.parse_mention(
                                            mention
                                            )
                                    response.append(mention)
                                    mentions.append(mention)
                                    response.append(message[j])
                                    i = j
                                    break
                    else:
                        response.append(message[i])

                    i += 1

            if len(response) != 0:
                return response, mentions
        
        if self.library.tools.getValue("ADD_MENTIONS").value:
            message_lenght = len(message)
            i = 0
            ment_obj = self.library.tools.getValue("MENTION")
            while i != message_lenght:
                if message[i].lower() in [*self.library.tools.getValue("MENTIONS").value, 
                                    *self.library.tools.getValue("MENTION_NAME_CASES").value] and len(response) == 0: 
                    response = [ment_obj]

                if message[i][0] == '[' and message[i].count('|') == 1:
                    if message[i].count(']') > 0:
                        mention = self.library.tools.parse_mention(
                                message[i][message[i].rfind('[') + 1:message[i].find(']')]
                                )
                        mentions.append(mention)
                    else:
                        for j in range(i, message_lenght):
                            if message[j].count(']') > 0:
                                last_string, message[j] = message[j][0:message[j].find(']')], message[j][message[j].find(']') + 1:]
                                mention = " ".join([*message[i:j], last_string])[1:]
                                mention = self.library.tools.parse_mention(
                                        mention
                                        )
                                mentions.append(mention)
                                i = j
                                break
                    
                i += 1

            if len(response) != 0:
                return response, mentions

        if not self.library.tools.getValue("ONLY_COMMANDS").value:
            response.append(self.library.tools.getValue("NOT_COMMAND"))
            return response, []

        return [], []


    def parse_package(self, event_package):
        if (not self.library.tools.getValue("ONLY_COMMANDS")) == (len(event_package.items) == 1):
            if event_package.type in self.library.event_supports.keys():
                itemscopy = event_package.items.copy()
                modules = [asyncio.ensure_future(self.library.modules[i].package_handler(self.library.tools, event_package), loop = self.thread_loop) for i in self.library.event_supports[event_package.type]]
                        
                self.library.tools.module = 'message_handler'
                
                reaction = self.thread_loop.run_until_complete(
                    asyncio.gather(*modules)
                    )
                if len(self.library.error_handlers) > 0:
                    if len(reaction) == 0:
                        reaction.append([self.library.tools.getValue("NOREACT")])

                    for i in reaction:
                        if isinstance(i, (list, tuple)):
                            if isinstance(i, tuple): i = list(i)
                            event_package.items = i

                            try:
                                if event_package.items[0] == self.library.tools.getValue("LIBRARY"):
                                    if event_package.items[1] == self.library.tools.getValue("LIBRARY_NOSELECT"):
                                        event_package.items[1] = [
                                            (e, self.library.modules[e].name) for e in self.library.modules.keys() if e not in self.library.hidden_modules
                                        ]

                                    elif event_package.items[1] == self.library.tools.getValue("LIBRARY_RELOAD"):
                                        self.library.upload(isReload = True, loop = self.thread_loop)
                                        event_package.items.append(self.library.tools.getValue("LIBRARY_SUCCESS"))

                                    elif event_package.items[1] in self.library.modules.keys():
                                        event_package.items.append(self.library.modules[event_package.items[1]].version)
                                        event_package.items.append(self.library.modules[event_package.items[1]].description)

                                    else:
                                        event_package.items[1] = self.library.tools.getValue("LIBRARY_ERROR")

                                    eh = [asyncio.ensure_future(self.library.modules[i].error_handler(self.library.tools, event_package), loop = self.thread_loop) for i in self.library.error_handlers]
                                    
                                    self.library.tools.module = 'error_handler'
                                    self.thread_loop.run_until_complete(asyncio.wait(eh))

                            except Exception as e:
                                self.library.tools.system_message(traceback.format_exc())
                    
                response = self.library.tools.getValue("MESSAGE_HANDLER_TYPE").value + '\n'
                if event_package.peer_id != event_package.from_id:
                    response += self.library.tools.getValue("MESSAGE_HANDLER_CHAT").value + '\n'

                response += self.library.tools.getValue("MESSAGE_HANDLER_USER").value + '\n'
                if self.library.tools.getValue("NOT_COMMAND") not in itemscopy and self.library.tools.ischecktype(itemscopy, objects.expression):
                    response += self.library.tools.getValue("MESSAGE_HANDLER_ITEMS").value + '\n'
                    itemscopy = [str(i) for i in itemscopy[:-1]]
                if event_package.text !='': response += self.library.tools.getValue("MESSAGE_HANDLER_IT").value + '\n'
                
                response = response.format(
                    peer_id = event_package.peer_id,
                    from_id = event_package.from_id,
                    event_type = event_package.type.value,
                    items = itemscopy,
                    text = "\t" + event_package.text.replace("\n", "\n\t\t\t")
                )
                self.library.tools.system_message(response, module = "message_handler")