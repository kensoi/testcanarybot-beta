class MethodError(Exception):
    pass

class LongpollError(MethodError):
    pass

class LoopStateError(Exception):
    pass
    
class LibraryError(Exception):
    pass

class DBError(LibraryError):
    pass