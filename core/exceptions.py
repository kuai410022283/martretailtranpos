class MRTPOSBaseException(Exception):
    def __init__(self, message=""):
        self.message = message
        super().__init__(self.message)

class DatabaseError(MRTPOSBaseException):
    pass

class ModuleLoadError(MRTPOSBaseException):
    pass

class DependencyError(MRTPOSBaseException):
    pass

class ServiceNotFoundError(MRTPOSBaseException):
    pass

class InsufficientStockError(MRTPOSBaseException):
    pass

class InvalidProductError(MRTPOSBaseException):
    pass

class MemberNotFoundError(MRTPOSBaseException):
    pass

class AuthenticationError(MRTPOSBaseException):
    pass

class AuthorizationError(MRTPOSBaseException):
    pass
