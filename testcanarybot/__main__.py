import argparse
import os
import string
import random

from .source.manager import *

parser = argparse.ArgumentParser(description='manager for testcanarybot')
parser.add_argument("-c", dest="create_module", action = 'store_true', help='create a testcanarybot 0.7 module')

parser.add_argument("--name", type=str, default='', help='create module in a folder')
parser.add_argument("-m", dest="manually", action = 'store_true', help='write details manually')
parser.add_argument("-f", dest="folder", action = 'store_true', help='create module in a folder')
parser.add_argument("-ph", dest="package_handler", action = 'store_true', help='parser for package')
parser.add_argument("-eh", dest="error_handler", action = 'store_true', help='parser for errors')

args = parser.parse_args()


for filename in ['\\assets\\', '\\library\\']:
    try:
        os.mkdir(os.getcwd() + filename)
    except:
        pass


def parsename(name: str):
    name = name.lower()
    test, i = len(name), 0
    while i< test:
        if name[i] not in [
                *string.ascii_lowercase,
                *string.digits]:
            name = name[:i] + name[i+1:]
            test -= 1

        else:
            i+= 1

    if name == '': name = gen_str()
    
    return name


def __write(file_dest, var):
    if file_dest.endswith("main.py"):
        folder = file_dest[:file_dest.rfind("\\")]
        if not os.path.exists(folder): os.mkdir(folder)

    with open(file_dest, mode="w+", encoding="utf-8") as new_file:
        new_file.write(var)


def bool_str(line: str):
    if line.lower() in ['true', '1', 'правда', 'y', 'yes', 'да']:
        return True

    elif line.lower() in ['false', '1', 'ложь', 'n', 'no', 'нет']:
        return False

    else:
        raise ValueError("Wrong string")


def gen_str(test = None):
    result, num = "", random.randint(5, 25)

    if isinstance(test, int):
        num = test

    for i in range(num):
        result += random.choice([
                *string.ascii_lowercase,
                *string.digits]
        )
    return result


if args.create_module:
    render = module_cover

    descr, descr_line = str(), ":::TESTCANARYBOT:DESCR_LINE:::"
    dest = '\\library\\{codename}{folder}.py'

    if args.manually:
        print(f"Hello! it's a manager for testcanarybot!")
        name = input("Enter a name for your plugin: ") if args.name == '' else args.name

        print("Enter a description for your plugin: ")
        codename = parsename(name)
        descr, descr_line = str(), ":::TESTCANARYBOT:DESCR_LINE:::"

        if args.folder:
            dest = f'\\library\\{codename}\\main.py'
        
        else:
            dest = f'\\library\\{codename}.py'

        while descr_line != "":
            descr_line = input("\t")
            descr += descr_line

            if descr_line != "":
                descr += '\n' +  " " * 12

        if descr == '': descr = 'Look at this string, you can use it like a password: ' + gen_str() + '\n' +  " " * 12

        if args.folder:
            dest = dest.format(
                codename = codename,
                folder = '\\main'
                )
        
        else:
            ans = input("Create module in a folder? [y/n] \n>> ")
            ans = bool_str(ans)

            if ans:
                dest = dest.format(
                    codename = codename,
                    folder = '\\main'
                    )

            else:
                dest = dest.format(
                    codename = codename,
                    folder = ''
                    )

        if args.package_handler:
            render = render.format(
                name = '{name}',
                descr = '{descr}',
                package_events = package_events, 
                package_handler = package_handler,
                package_handler_import = package_handler_import,
                error_handler = "{error_handler}"
                )

        else:
            ans = input("Create a package_handler in a module? [y/n] \n>> ")
            ans = bool_str(ans)

            if ans:
                render = render.format(
                    name = '{name}',
                    descr = '{descr}',
                    package_events = package_events, 
                    package_handler = package_handler,
                    package_handler_import = package_handler_import,
                    error_handler = "{error_handler}"
                    )
            else:
                render = render.format(
                    name = '{name}',
                    descr = '{descr}',
                    package_events = "", 
                    package_handler = "",
                    package_handler_import = "",
                    error_handler = "{error_handler}"
                    )

        if args.error_handler:
            render = render.format(
                    name = '{name}',
                    descr = '{descr}',
                    error_handler = error_handler
                    )

        else:
            ans = input("Create a package_handler in a module? [y/n] \n>> ")
            ans = bool_str(ans)
            if ans:
                render = render.format(
                    name = '{name}',
                    descr = '{descr}',
                    error_handler = error_handler
                    )
            else:
                render = render.format(
                    name = '{name}',
                    descr = '{descr}',
                    error_handler = "{error_handler}"
                    )


    else:
        name =  "module" + gen_str() if args.name == '' else args.name
        codename = parsename(name)
        descr = 'Look at this string, you can use it like a password: ' + gen_str() + '\n' +  " " * 12
        
        if args.folder:
            dest = dest.format(
                codename = codename,
                folder = '\\main'
                )
        
        else:
            dest = dest.format(
                codename = codename,
                folder = ''
                )

        if args.package_handler:
            render = render.format(
                name = '{name}',
                descr = '{descr}',
                package_events = package_events, 
                package_handler = package_handler,
                package_handler_import = package_handler_import,
                error_handler = "{error_handler}"
                )

        else:
            render = render.format(
                name = '{name}',
                descr = '{descr}',
                package_events = "", 
                package_handler = "",
                package_handler_import = "",
                error_handler = "{error_handler}"
                )

        if args.error_handler:
            render = render.format(
                name = '{name}',
                descr = '{descr}',
                error_handler = error_handler
                )

        else:
            render = render.format(
                name = '{name}',
                descr = '{descr}',
                error_handler = ""
                )  

    render = render.replace("{name}", name)
    render = render.replace("{descr}", descr)

    test = os.getcwd() + dest
    __write(test, render)
        
    print(f"Executed! [{test}]")     