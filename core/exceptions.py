from abc import ABC


class BaseCustomException(Exception, ABC):
    """
    Base class for all custom exceptions.
    """
    
    def __init__(self, message: str | None = None):
        self.message = message or self.get_default_message()
        super().__init__(self.message)
    
    def get_default_message(self) -> str:
        """
        Return default error message.
        
        Returns
        -------
        str
            Default error message
        """
        return "error.unknown"
    
    def get_status_code(self) -> int:
        """
        Return HTTP status code for exception.
        
        Returns
        -------
        int
            HTTP status code
        """
        return 500


class BadRequestException(BaseCustomException):
    """Bad request exception (400)."""
    
    def get_status_code(self) -> int:
        return 400


class NotFoundException(BaseCustomException):
    """Not found exception (404)."""
    
    def get_status_code(self) -> int:
        return 404


class NetworkNotSupportedException(BadRequestException):
    """Network not supported exception."""
    
    def get_default_message(self) -> str:
        return "error.network.not_supported"


class InvalidAddressException(BadRequestException):
    """Invalid address exception."""
    
    def get_default_message(self) -> str:
        return "error.address.invalid"


class RPCException(BaseCustomException):
    """RPC error exception."""
    
    def get_default_message(self) -> str:
        return "error.rpc.failed"


class ABIFetchException(BaseCustomException):
    """ABI fetch error exception."""
    
    def get_default_message(self) -> str:
        return "error.abi.fetch_failed"

