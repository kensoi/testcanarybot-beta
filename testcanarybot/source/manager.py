from .versions_list import supporting
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
