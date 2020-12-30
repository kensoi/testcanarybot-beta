from .versions_list import supporting
module_cover = """from testcanarybot import objects{package_handler_import}

class Main(objects.libraryModule):
    async def start(self, tools: objects.tools):
        self.name = "{name}" # optional
        self.version = """ + str(supporting[-1]) + """ # optional
        self.description = \"\"\"
            {descr}\"\"\" # optional{package_events}
        
        {package_handler}{error_handler}
"""

package_events = """
        self.packagetype = [
            events.message_new
        ]"""

package_handler = """
    async def package_handler(self, tools: objects.tools, package: objects.package):
        # tools: testcanarybot.tools
        # package: formatted into message object got from longpoll server
        pass

"""
package_handler_import = ", events # for Main.package_handler"

error_handler = """
    async def error_handler(self, tools: objects.tools, package: objects.package):
        # tools: testcanarybot.tools
        # package: formatted into message object got from longpoll server
        pass
"""
