class BusinessError(Exception):
    """Base exception for business logic errors."""
    pass


class RideError(BusinessError):
    """Raised when a ride operation fails."""
    pass


class DriverError(BusinessError):
    """Raised when a driver operation fails."""
    pass


class FareError(BusinessError):
    """Raised when fare calculation fails."""
    pass
