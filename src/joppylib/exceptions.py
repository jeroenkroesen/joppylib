"""Custom exceptions for JopPyLib
"""


class AuthorizationDeniedError(Exception):
    """The Joplin user has explicitly denied a request for an API token
    """
    pass
