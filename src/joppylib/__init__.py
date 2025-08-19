"""Python wrapper for the Joplin Data Api
"""
from . import config, connection, api_client, defaults, exceptions, joplin_client
from .joplin_client import JoplinClient
from .api_client import APIClient

# Instantiate default JopPyLib
default_settings = config.Settings()


__all__ = [
    'config',
    'default_settings',
    'connection',
    'api_client',
    'APIClient',
    'joplin_client',
    'JoplinClient',
    'defaults',
    'exceptions'
]
