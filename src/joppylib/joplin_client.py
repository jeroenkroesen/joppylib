"""Higher level interface to the API
"""

from typing import Optional, Any, Dict, List

import requests

from .connection import (
    check_connection,
    get_auth_token
)
from .api_client import APIClient
from .config import Settings
from .exceptions import AuthorizationDeniedError



class Item:
    """Abstract functionality for Joplin items (ex: notes etc)
    """
    def __init__(
        self,
        name: str,
        settings: Settings,
        api_key: str,
        api_client: APIClient
    ) -> None:
        self.name = name
        self.settings = settings
        self.__api_key = api_key
        self.__api_client = getattr(api_client, self.name)


    def search(
        self,
        query: str,
        fields: Optional[ List[str] ] = None, 
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None,
        debug: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Search using the Joplin search syntax

        Parameters
        ----------
        query : str
            The search query. See the Joplin API for query syntax
        fields: List[str] (optional)
            A list of object fields to include in the results.
            Fields will be checked against the item type's allowed fields.
        order_by : str (optional)
            A field to order the results by. If specified, 
            the field will be checked against allowed fields for the 
            item type.
        order_dir : str (optional)
            "ASC" or "DESC" to specify order direction.
        debug : bool (optional, default: False)
            If True, include all requests responses in the response.

        Returns
        -------
        Dict
            The result of the search query. With the following keys:
            success : bool
                True if all requests had status 200
            error : str (optional)
                If success is False, this will contain an 
                error description.
            data : list (optional)
                Data returned from the api if success is True
            responses : list (optional)
                Requests response objects for each API call.
                Only added if debug is True.

        See also
        --------
        api_client.py
            Lower-level implementation called by this method
        """
        return self.__api_client.search(
            self.__api_key,
            self.settings,
            query,
            fields,
            order_by,
            order_dir,
            debug
        )
    
    
    def get_multi(
        self,  
        fields: Optional[ List[str] ] = None, 
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None,
        debug: Optional[bool] = False
    ) -> Dict[str,Any]:
        """Get a list of all items

        Parameters
        ----------
        fields: List[str]
            Optional. A list of object fields to include in the results
            Fields will be checked against the item types allowed fields
        order_by : str
            Optional. A field to order the results by. If specified, 
            the field will be checked against allowed fields for the 
            item type.
        order_dir : str
            Optional. "ASC" or "DESC" to specify order direction.
        debug : bool (optional, default: False)
            If True, include all requests responses in the response.

        Returns
        -------
        Dict
            The result of the search query. With the following keys:
            success : bool
                True if all requests had status 200
            error : str (optional)
                If success is False, this will contain an 
                error description.
            data : list (optional)
                Data returned from the api if success is True
            responses : list (optional)
                Requests response objects for each API call.
                Only added if debug is True.
        
        See also
        --------
        api_client.py
            Lower-level implementation called by this method.
        """
        return self.__api_client.get_multi(
            self.__api_key,
            self.settings,
            fields,
            order_by,
            order_dir,
            debug
        )
    
    
    def get(
        self, 
        id: str,
        fields: Optional[ List[str] ] = None
    ) -> requests.Response:
        """Get an entity instance by ID

        Parameters
        ----------
        id : str
            The ID of the item to get
        fields: List[str]
            Optional. A list of object fields to include in the results.
            Fields will be checked against the item types allowed fields.

        Returns
        -------
        requests.Response
            The response object fromt the request.
            To access it's contents, call response.json() to extract data.

        See also
        --------
        api_client.py
            Lower-level implementation called by this method.
        """
        return self.__api_client.get(
            self.__api_key,
            self.settings,
            id,
            fields
        )
    
    
    def create(
        self, 
        data: Dict[str, Any] | str
    ) -> requests.Response:
        """POST a new entity to the api. 
        
        Parameters
        ----------
        data : Dict[str, Any] | str
            The data for the object to create. Some objects, like tags, can be 
            created by passing their title as a string. If a dict is passed 
            it must contain at least the all the required fields as its keys.

        Returns
        -------
        requests.Response
            The response object of the request.
            Call response.json() to access it's data.

        See also
        --------
        api_client.py
            Lower-level implementation called by this method.
        """
        return self.__api_client.create(
            self.__api_key,
            self.settings,
            data
        )
    
    
    def update(
        self,  
        data: Dict[str, Any]
    ) -> requests.Response:
        """Update an existing entity 
        
        Parameters
        ----------
        data : Dict[str, Any]
            The data for the object to create.

        Returns
        -------
        requests.Response
            The response object of the request.
            Call response.json() to access it's data.
        See also
        --------
        api_client.py
            Lower-level implementation called by this method.
        """
        return self.__api_client.update(
            self.__api_key,
            self.settings,
            data
        )



class Note(Item):
    """Interact with notes
    """
    name: str = 'note'

    def get_all_tags(
        self,
        note_id: str,
        debug: Optional[bool] = False
    ) -> Dict[str,Any]:
        """Get all tags attached to this note

        Parameters
        ----------
        note_id : str
            ID of the note to get all tags for.
        debug : bool (optional, default: False)
            If True, include all requests responses in the response.

        Returns
        -------
        Dict
            The result of the query, with the following keys:
            success : bool
                True if all requests had status 200
            error : str (optional)
                If success is False, this will contain an 
                error description.
            data : list (optional)
                Data returned from the api if success is True
            responses : list (optional)
                Requests response objects for each API call.
                Only added if debug is True.
        """
        return self.__api_client.get_all_tags(
            self.__api_key,
            self.settings,
            note_id,
            debug
        )



class Tag(Item):
    """Interact with items
    """
    name: str = 'tag'

    def add_to_note(
        self, 
        tag_id: str, 
        note_id: str
    ) -> requests.Response:
        """Add this tag to a note

        Parameters
        ----------
        tag_id : str
            The ID of the tag to add to the note
        note_id : str
            The ID of the note to add this tag to.

        Returns
        -------
        requests.Response
            The response object of the request. 
            Call response.json() to access it's data.
        """
        return self.__api_client.add_to_note(
            self.__api_key,
            self.settings,
            tag_id,
            note_id
        )


    def remove_from_note(
        self, 
        tag_id: str, 
        note_id: str
    ) -> requests.Response:
        """Remove this tag from a note

        Parameters
        ----------
        tag_id : str
            The ID of the tag to remove from note
        note_id : str
            The ID of the note to remove this tag from.

        Returns
        -------
        requests.Response
            The response object of the request. 
            Call response.json() to access it's data.
        """
        return self.__api_client.remove_from_note(
            self.__api_key,
            self.settings,
            tag_id,
            note_id
        )






class JoplinClient:
    """Higher level interface to the Joplin API
    """
    def __init__(
        self,
        settings: Settings,
        auth_method: str = 'interactive', # 'key' or 'interactive'
        api_key: Optional[str] = None
    ) -> None:
        self.settings = settings
        # ---Authenticate---
        if auth_method not in ['key', 'interactive']:
            m = f'auth_method can be "key" or "interactive", not {auth_method}'
            raise ValueError(m)
        if auth_method == 'key':
            if not api_key:
                m = 'api_key is required if auth_method = "key"'
                raise ValueError(m)
            self.__api_key = api_key
        elif auth_method == 'interactive':
            authenticated = self.authenticate()
            if not authenticated:
                m = 'User has denied access to Joplin'
                raise AuthorizationDeniedError(m)
        # ---Instanticate Item interfaces---
        client = APIClient()
        self.note = Note('note', settings, self.__api_key, client)
        self.tag = Tag('tag', settings, self.__api_key, client)
        self.folder = Item('folder', settings, self.__api_key, client)
        self.event = Item('event', settings, self.__api_key, client)
        self.resource = Item('resource', settings, self.__api_key, client)
        self.revision = Item('revision', settings, self.__api_key, client)


    def authenticate(self) -> bool:
        """Request an api key from the user via Joplin
        """
        if check_connection(
            self.settings.base_url, self.settings.ping_route
        ):
            result = get_auth_token(
                self.settings.base_url, 
                self.settings.auth_init_route, 
                self.settings.auth_check_route
            )
            if result['status'] == 'accepted':
                self.__api_key = result['token']
                return True
            else: 
                return False
        else:
            msg = 'Joplin Data API not available'
            raise requests.exceptions.ConnectionError(msg)
