"""All errors raised by opsclient. Catch OpsClientError to catch every one of them."""


class OpsClientError(Exception):
    """Base class for every opsclient error."""


class OpsConnectionError(OpsClientError):
    """The server could not be reached, or it took too long to answer."""


class OpsApiError(OpsClientError):
    """The server answered with an error status code."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code


class OpsNotFoundError(OpsApiError):
    """The server answered 404: the thing you asked for does not exist."""


class OpsValidationError(OpsClientError):
    """The server's answer did not have the shape we expected."""
