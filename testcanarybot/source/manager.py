from .versions_list import supporting
module_cover = """from testcanarybot import objects
from testcanarybot.events import events # for Main.package_handler

class Main(objects.libraryModule):
    async def start(self, tools: objects.tools):
        self.packagetype = [
            events.message_new
        ]
        
        
    async def package_handler(self, tools: objects.tools, package: objects.package):
        \"\"\"
        :tools: 
        \"\"\""""