"""CRUD for the Joplin Data API
"""

from typing import Dict, List, Optional, Any
import requests

from .config import Settings


class Item:
    """A generic implementation of a Joplin item type
    To be used for interaction with the Webclipper API.

    Attributes
    ----------
    name : str
        The name of the API entity
    route : str
        The API route to interact with this entity
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    """
    name: str = ''
    route: str = ''
    fields: List[str] = []
    fields_create_required: List[str] = []


    def fields_to_params(self, fields: List[str], check: bool = True) -> str:
        """Concat list of fields into csv str for use in url parameters
        Optionally check if the fields are in self.fields (default: true)

        Parameters
        ----------
        fields : List[str]
            The fields as a list of strings.
        check : bool
            If true, check if the fields contains any fields that are not in 
            the items defined fields.
        """
        for field in fields:
            if check:
                if field not in self.fields:
                    msg = f'{field} is not an allowed field for {self.name}'
                    raise ValueError(msg)
        return f'{",".join(fields)}'

    
    def search(
        self, 
        api_key: str, 
        settings: Settings, 
        query: str,
        fields: Optional[ List[str] ] = None, 
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None,
        debug: Optional[bool] = False
    ) -> Dict[str, Any]:
        """Search using the API

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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

        Raises
        ------
        ValueError
            If order_by is a field name that is not in self.fields
            If order_dir is not either "ASC" or "DESC"
        """
        # Setup params
        ## Fixed params
        params = f'?query={query}'
        # Default assumes we're searching notes. If not, the item type must 
        #  be added to the parameters
        if self.name != 'note':
            params += f'&type={self.name}'
        params += f'&token={api_key}&limit={settings.pagesize}'
        ## Optional params
        if fields:
            # validate fields in list and turn into comma-separated string
            fieldnames = self.fields_to_params(fields)
            params += f'&fields={fieldnames}'
        if order_by:
            if order_by not in self.fields:
                msg = f'{order_by} is not a valid field to order by'
                raise ValueError(msg)
            params += f'&order_by={order_by}'
        if order_dir:
            if order_dir not in ['ASC', 'DESC']:
                msg = f'{order_dir} is not valid. Use ASC or DESC'
                raise ValueError(msg)
            params += f'&order_dir={order_dir}'
        # Base url: url without pagination
        base_url = f'{settings.base_url}/{settings.search_route}{params}'
        # Setup datastructure for return to caller
        final_result = {} # dict to return to caller
        final_result['success'] = True # Assume success until encounter problem
        result_data = [] # Concat data here
        result_responses = [] # Store requests responses here for debug
        req_nr = 1 # Request nr
        req_index = 0
        has_more = True # Make sure request is performed at least once
        url = f'{base_url}&page={req_nr}' # Add pagination to url
        while has_more: # Loop until pagination completes
            result_responses.append(requests.get(url)) # Perform request
            if result_responses[req_index].status_code == 200: # Success: get data
                resp_data = result_responses[req_index].json() # Extract data
                result_data.extend(resp_data['items']) # Add to total data to return
                has_more = resp_data['has_more'] # Check if more data exists
                req_nr += 1 # Increase request counter
                req_index += 1
                url = f'{base_url}&page={req_nr}' # Update URL for next page
            else:
                final_result['success'] = False
                msg = f'Request nr {req_nr} failed with status code: {result_responses[req_index].status_code}'
                final_result['error'] = msg
                break
        if final_result['success']:
            final_result['data'] = result_data
        if debug:
            final_result['responses'] = result_responses
        return final_result

    
    def get_multi(
        self, 
        api_key: str, 
        settings: Settings, 
        fields: Optional[ List[str] ] = None, 
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None,
        debug: Optional[bool] = False
    ) -> Dict[str,Any]:
        """Get a list of all items

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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

        Raises
        ------
        ValueError
            If order_by is a field name that is not in self.fields
            If order_dir is not either "ASC" or "DESC"
        """
        # Setup request parameters
        ## Fixed params
        params = f'?token={api_key}&limit={settings.pagesize}'
        ## Optional params
        if fields:
            fieldnames = self.fields_to_params(fields)
            params += f'&fields={fieldnames}'
        if order_by:
            if order_by not in self.fields:
                msg = f'{order_by} is not a valid field to order by'
                raise ValueError(msg)
            params += f'&order_by={order_by}'
        if order_dir:
            if order_dir not in ['ASC', 'DESC']:
                msg = f'{order_dir} is not valid. Use ASC or DESC'
                raise ValueError(msg)
            params += f'&order_dir={order_dir}'
        # Url setup
        base_url = f'{settings.base_url}/{self.route}{params}'
        # Setup datastructure for return to caller
        final_result = {} # dict to return to caller
        final_result['success'] = True # Assume success until encounter problem
        result_data = [] # Concat data here
        result_responses = [] # Store requests responses here for debug
        req_nr = 1 # Request nr
        req_index = req_nr - 1
        has_more = True # Make sure request is performed at least once
        url = f'{base_url}&page={req_nr}' # Add pagination to url
        while has_more: # Loop until pagination completes
            result_responses.append(requests.get(url)) # Perform request
            if result_responses[req_index].status_code == 200: # Success: get data
                resp_data = result_responses[req_index].json() # Extract data
                result_data.extend(resp_data['items']) # Add to total data to return
                has_more = resp_data['has_more'] # Check if more data exists
                req_nr += 1 # Increase request counter
                req_index += 1
                url = f'{base_url}&page={req_nr}' # Update URL for next page
            else:
                final_result['success'] = False
                msg = f'Request nr {req_nr} failed with status code: {result_responses[req_index].status_code}'
                final_result['error'] = msg
                break
        if final_result['success']:
            final_result['data'] = result_data
        if debug:
            final_result['responses'] = result_responses
        return final_result


    def get(
        self, 
        api_key: str, 
        settings: Settings, 
        id: str,
        fields: Optional[ List[str] ] = None
    ) -> requests.Response:
        """Get an entity instance by ID

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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
        """
        # Setup request parameters
        params = f'?token={api_key}' ## Default params
        ## Optional params
        if fields:
            fieldnames = self.fields_to_params(fields)
            params += f'&fields={fieldnames}'
        # Url setup
        url = f'{settings.base_url}/{self.route}/{id}{params}'
        return requests.get(url)
   

    def create(
        self, 
        api_key: str, 
        settings: Settings, 
        data: Dict[str, Any] | str
    ) -> requests.Response:
        """POST a new entity to the api. 
        
        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
        data : Dict[str, Any] | str
            The data for the object to create. Some objects, like tags, can be 
            created by passing their title as a string. If a dict is passed 
            it must contain at least the all the required fields as its keys.

        Returns
        -------
        requests.Response
            The response object of the request.
            Call response.json() to access it's data.

        Raises
        ------
        ValueError
            If data is a dict and a required field is not found among 
            its keys.
        """
        # Make sure minimum fields are present in data
        ## Notes need a dict with fields as payload. Other entities can often 
        ## be created with just their name in string.
        if isinstance(data, dict):
            for field in self.fields_create_required:
                if field not in data.keys():
                    msg = f'Required field {field} was not found in data.'
                    raise ValueError(msg)
        params = f'?token={api_key}' # Setup request parameters
        url = f'{settings.base_url}/{self.route}{params}' # Setup url
        return requests.post(url, json=data) # Perform request


    def update(
        self, 
        api_key: str, 
        settings: Settings,
        id: str,
        data: Dict[str, Any]
    ) -> requests.Response:
        """Update an existing entity 
        
        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
        id: str
            The ID of the item to update
        data : Dict[str, Any]
            The data for the object to create.

        Returns
        -------
        requests.Response
            The response object of the request.
            Call response.json() to access it's data.

        Raises
        ------
        ValueError
            If data is a dict and a required field is not found among 
            its keys.
        """
        params = f'?token={api_key}' # Setup request parameters
        url = f'{settings.base_url}/{self.route}/{id}{params}' # Setup url
        return requests.put(url, json=data) # Perform request
    
    
    def delete(
        self, 
        api_key: str, 
        settings: Settings, 
        id: str,
        trash: Optional[bool] = True
    ) -> requests.Response:
        """Get an entity instance by ID

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
        id : str
            The ID of the item to get
        trash : bool (default: True)
            If True, move the note to trash. If false, permanently 
            delete it.

        Returns
        -------
        requests.Response
            The response object fromt the request.
            There will be no json content
        """
        # Setup request parameters
        params = f'?token={api_key}' ## Default params
        if not trash:
            params += '&permanent=1'
        # Url setup
        url = f'{settings.base_url}/{self.route}/{id}{params}'
        return requests.delete(url)



class Note(Item):
    """Interact with notes in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "note".
        This object deals with notes. 
    route : str
        Default: "notes".
        The API route to interact with notes.
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    """
    name: str = 'note'
    route: str = 'notes'
    fields_create_required: List[str] = ['title', 'body', 'parent_id']
    fields: List[str] = [ # https://joplinapp.org/help/api/references/rest_api/#notes
        'id',
        'parent_id',
        'title',
        'body',
        'created_time',
        'updated_time',
        'is_conflict',
        'latitude',
        'longitude',
        'altitude',
        'author',
        'source_url',
        'is_todo',
        'todo_due',
        'todo_completed',
        'source',
        'source_application',
        'application_data',
        'order',
        'user_created_time',
        'user_updated_time',
        'encryption_cipher_text',
        'encryption_applied',
        'markup_language',
        'is_shared',
        'share_id',
        'conflict_original_id',
        'master_key_id',
        'user_data',
        'deleted_time',
        'body_html',
        'base_url',
        'image_data_url',
        'crop_rect'
    ]

    def get_all_tags(
        self,
        api_key: str,
        settings: Settings,
        note_id: str,
        debug: Optional[bool] = False
    ) -> Dict[str,Any]:
        """Get all tags attached to this note

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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
        # Setup request parameters
        ## Fixed params
        params = f'?token={api_key}&limit={settings.pagesize}'
        # Url setup
        base_url = f'{settings.base_url}/{self.route}/{note_id}/tags{params}'
        # Setup datastructure for return to caller
        final_result = {} # dict to return to caller
        final_result['success'] = True # Assume success until encounter problem
        result_data = [] # Concat data here
        result_responses = [] # Store requests responses here for debug
        req_nr = 1 # Request nr
        req_index = req_nr - 1
        has_more = True # Make sure request is performed at least once
        url = f'{base_url}&page={req_nr}' # Add pagination to url
        while has_more: # Loop until pagination completes
            result_responses.append(requests.get(url)) # Perform request
            if result_responses[req_index].status_code == 200: # Success: get data
                resp_data = result_responses[req_index].json() # Extract data
                result_data.extend(resp_data['items']) # Add to total data to return
                has_more = resp_data['has_more'] # Check if more data exists
                req_nr += 1 # Increase request counter
                req_index += 1
                url = f'{base_url}&page={req_nr}' # Update URL for next page
            else:
                final_result['success'] = False
                msg = f'Request nr {req_nr} failed with status code: {result_responses[req_index].status_code}'
                final_result['error'] = msg
                break
        if final_result['success']:
            final_result['data'] = result_data
        if debug:
            final_result['responses'] = result_responses
        return final_result



class Tag(Item):
    """Interact with tags in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "tag".
        This object deals with tags.
    route : str
        Default: "tags".
        The API route to interact with tags
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    """
    name: str = 'tag'
    route: str = 'tags'
    fields_create_required: List[str] = ['title']
    fields: List[str] = [
        'id',
        'title',
        'created_time',
        'updated_time',
        'user_created_time',
        'user_updated_time',
        'encryption_cipher_text',
        'encryption_applied',
        'is_shared',
        'parent_id',
        'user_data'
    ]


    def add_to_note(
        self, 
        api_key: str, 
        settings: Settings, 
        tag_id: str, 
        note_id: str
    ) -> requests.Response:
        """Add this tag to a note

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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
        params = f'?token={api_key}' # Setup request parameters
        # Setup URL
        url = f'{settings.base_url}/{self.route}/{tag_id}/notes{params}'
        data = {'id': note_id} # Setup request payload
        return requests.post(url, json=data) # Perform request


    def remove_from_note(
        self, 
        api_key: str, 
        settings: Settings, 
        tag_id: str, 
        note_id: str
    ) -> requests.Response:
        """Remove this tag from a note

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
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
        params = f'?token={api_key}' # Setup request parameters
        # Setup URL
        url = f'{settings.base_url}/{self.route}/{tag_id}/notes/{note_id}{params}'
        return requests.delete(url) # Perform request



class Folder(Item):
    """Interact with folders (notebooks) in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "folder".
        This object deals with folders. 
    route : str
        Default: "folders".
        The API route to interact with folders
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    """
    name: str = 'folder'
    route: str = 'folders'
    fields_create_required: List[str] = ['title', 'parent_id']
    fields: List[str] = [
        'id',
        'title',
        'created_time',
        'updated_time',
        'user_created_time',
        'user_updated_time',
        'encryption_cipher_text',
        'encryption_applied',
        'parent_id',
        'is_shared',
        'share_id',
        'master_key_id',
        'icon',
        'user_data',
        'deleted_time'
    ]



class Resource(Item):
    """Interact with resources in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "resource".
        This object deals with resources. 
    route : str
        Default: "resources".
        The API route to interact with resources
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.

    """
    name: str = 'resource'
    route: str = 'resources'
    fields_create_required: List[str] = ['title', 'parent_id']
    fields: List[str] = [
        'id',
        'title',
        'mime',
        'filename',
        'created_time',
        'updated_time',
        'user_created_time',
        'user_updated_time',
        'file_extension',
        'encryption_cipher_text',
        'encryption_applied',
        'encryption_blob_encrypted',
        'size',
        'is_shared',
        'share_id',
        'master_key_id',
        'user_data',
        'blob_updated_time',
        'ocr_text',
        'ocr_details',
        'ocr_status',
        'ocr_error'
    ]
    # TODO: Override POST function to deal with resource specifics
    ## Posting already works for notes, tags and notebooks. 
    ## Probably needs overriding for resources. 



class Revision(Item):
    """Interact with Revisions in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "revision".
        This object deals with revisions. 
    route : str
        Default: "revisions".
        The API route to interact with revisions.
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    """
    name: str = 'revision'
    route: str = 'revisions'
    fields_create_required: List[str] = ['parent_id']
    fields: List[str] = [
        'id',
        'parent_id',
        'item_type',
        'item_id',
        'item_updated_time',
        'title_diff',
        'body_diff',
        'metadata_diff',
        'encryption_cipher_text',
        'encryption_applied',
        'updated_time',
        'created_time',
    ]



class Event(Item):
    """Interact with Events in Joplin via the webclipper API

    Attributes
    ----------
    name : str
        Default: "event".
        This object deals with events. 
    route : str
        Default: "events".
        The API route to interact with events
    fields_create_required : List[str]
        The fields that are required by the API for a successfull POST request
    fields: List[str]
        A list of fields that the entity may have according to the Joplin 
        documentation.
    """
    name: str = 'event'
    route: str = 'events'
    fields: List[str] = [
        'id',
        'item_type',
        'item_id',
        'type',
        'created_time',
        'source',
        'before_change_item',
    ]




class APIClient:
    """Low-level client for the Joplin Data API
    """
    def __init__(self) -> None:
        self.note = Note()
        self.tag = Tag()
        self.folder = Folder()
        self.event = Event()
        self.resource = Resource()
        self.revision = Revision()
