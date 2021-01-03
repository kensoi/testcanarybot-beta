module_cover = """from testcanarybot import objects
from testcanarybot.enums import events # for Main.package_handler

class Main(objects.libraryModule):
    async def start(self, tools: objects.tools):
        self.packagetype = [
            events.message_new
        ]
        
        
    async def package_handler(self, tools: objects.tools, package: objects.package):
        \"\"\"
        tools [objects.tools] - instruments
        package [objects.package] - your event.
        \"\"\"

        pass
        
    \"\"\"
    you can paste handlers like these:
    
    @objects.libraryModule.void
    async def {handler_name}(self, tools: objects.tools, package: objects.package):
        # tools [objects.tools] - instruments
        # package [objects.package] - your event.

        pass

    @objects.libraryModule.priority(commands = $list of commands from package.items[0]$)
    async def {handler_name}(self, tools: objects.tools, package: objects.package):
        # tools [objects.tools] - instruments
        # package [objects.package] - your event.

        pass
    \"\"\"
        """