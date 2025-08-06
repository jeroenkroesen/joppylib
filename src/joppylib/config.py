"""Settings and constants for joppylib
"""
from pydantic_settings import BaseSettings
from pydantic import computed_field



class Settings(BaseSettings):
    """Settings for Joplin Data API

    Defaults are from Joplin documentation.
    """
    protocol: str = 'http://'
    host: str = 'localhost'
    port: str = '41184'
    pagesize: int = 100
    ping_route: str = 'ping'
    auth_init_route: str = 'auth'
    auth_check_route: str = 'auth/check'
    search_route: str = 'search'
    
    @computed_field
    @property
    def base_url(self) -> str:
        return f'{self.protocol}{self.host}:{self.port}'
