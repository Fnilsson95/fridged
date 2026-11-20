"""Domain errors - what can go wrong in the business rules

Services will raise these instead of HTTP errors. HTTP error only says how to tell a web client

    * NotFoundError --> 404 Not Found
    * ConflictError --> 409 Conflict (allowed input, but wrong state)
    * InvalidRequestError --> 422 Unprocessable Content (input not compatible, breaks rules)
"""


class DomainError(Exception):
    """Base class for all errors the API should report to the client"""


class NotFoundError(DomainError):
    """Something the request referes to does not exist"""


class ConflictError(DomainError):
    """The request is valid, but not allowed in the current state"""


class InvalidRequestError(DomainError):
    """The request breaks the rules of input"""
