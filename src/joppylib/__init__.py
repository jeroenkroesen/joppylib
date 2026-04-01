"""Python wrapper for the Joplin Data Api"""

from importlib.metadata import version

from . import config, connection, api_client, exceptions, joplin_client
from .joplin_client import JoplinClient
from .api_client import APIClient

__version__ = version("joppylib")

# Instantiate default JopPyLib
default_settings = config.Settings()


__all__ = [
    "__version__",
    "config",
    "default_settings",
    "connection",
    "api_client",
    "APIClient",
    "joplin_client",
    "JoplinClient",
    "exceptions",
]
