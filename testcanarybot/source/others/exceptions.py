class MethodError(Exception):
    pass

class LongpollError(MethodError):
    pass

class LoopStateError(Exception):
    pass
    
class LibraryError(Exception):
    pass

class LibraryException(LibraryError):
    pass

class LibraryReload(LibraryException):
    pass

class Quit(LibraryException):
    pass

class DBError(LibraryError):
    pass