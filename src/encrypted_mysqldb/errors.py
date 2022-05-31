class Error(Exception):
    """Global error related to this package."""

    def __init__(self, mysql_error=None):
        self.mysql_error = mysql_error


class InvalidCryptError(Error):
    """Raised when the crypt object given for the Database initialization is invalid."""

    pass


class DatabaseInitializationError(Error):
    """Raised when the ConnectionPool of the Database could not be initialized."""

    pass


class NoConnectionAvailable(Error):
    """Raised when the ConnectionPool could not return a connection to the pool."""

    pass


class NotTableTypeError(Error):
    """Raised when using a method from the Database object with a variable that is not a subtype of Table."""

    pass


class NotImplementedError(Error):
    """Raised when a encryption method is used but has not beed defined."""

    pass


class InvalidTypeError(Error):
    """Raised when a Field is initialized with an invalid type."""

    pass


class ConversionError(Error):
    """Raised when the initial value of a Field could not be converted to the Field type."""

    pass


class SearchOnEncryptedFieldError(Error):
    """Raised when a query search is done with an encrypted field."""

    pass
