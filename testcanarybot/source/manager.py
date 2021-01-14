module_cover = """from testcanarybot import objects
from testcanarybot import enums # for Main.events

class Main(objects.libraryModule):
\tasync def start(self, tools: objects.tools):
\t\t\"\"\"
\t\tasync init for your module.

\t\ttools [objects.tools]: VK API methods (tools.api) and some useful functions by developer
\t\t\"\"\"
\t\t
\t\t
\t@objects.event(events = [enums.events.like_add]) # any event, excluding message_new.
\tasync def events_handler(self, tools: objects.tools, package: objects.package):
\t\t\"\"\"
\t\tThis is the handler for registered events.

\t\ttools [objects.tools]: VK API methods (tools.api) and some useful functions by developer
\t\tpackage [objects.package]: parsed package got from VK Bots Longpoll
\t\t\"\"\"
\t\tpass


\t@objects.void
\tasync def void_handler(self, tools: objects.tools, package: objects.package):
\t\t\"\"\"
\t\tThis is the handler for unregistered commands.

\t\ttools [objects.tools]: VK API methods (tools.api) and some useful functions by developer
\t\tpackage [objects.package]: parsed package got from VK Bots Longpoll
\t\t\"\"\"
\t\tpass


\t@objects.priority(commands = ["test1", "test2", "test3"])
\tasync def priority_handler(self, tools: objects.tools, package: objects.package):
\t\t\"\"\"
\t\tThis is the handler for these commands:
\t\t@yourbot test1 [items]
\t\t@yourbot test2 [items]
\t\t@yourbot test3 [items]
\t\t
\t\ttools [objects.tools]: VK API methods (tools.api) and some useful functions by developer
\t\tpackage [objects.package]: parsed package got from VK Bots Longpoll
\t\t\"\"\"

\t\tpass"""