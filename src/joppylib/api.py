"""Interacting with the Joplin Data API
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Any
import requests

if TYPE_CHECKING:
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
        order_dir: Optional[str] = None
    ) -> Dict[str, Any] | List[Any]:
        """Search using the API

        Parameters
        ----------
        api_key : str
            A valid API key to authenticate to the Joplin Data API
        settings : Settings
            A settings object from config.Settings
        query : str
            The search query. See the Joplin API for query syntax
        fields: List[str]
            Optional. A list of object fields to include in the results
            Fields will be checked against the item types allowed fields
        order_by : str
            Optional. A field to order the results by. If specified, 
            the field will be checked against allowed fields for the 
            item type.
        order_dir : str
            Optional. "ASC" or "DESC" to specify order direction.

        Returns
        -------
        Dict
            A dictionary with keys:
            "base_url": the full API call url, without pagination info.
            "result": the result of the search query.

        Raises
        ------
        ValueError
            If order_by is a field name that is not in self.fields
            If order_dir is not either "ASC" or "DESC"
        Exception
            If the API request returns with another status code than 200.
        """
        # Setup params
        ## Fixed params
        params = f'?query={query}'
        # Default assumes we're searching notes. If not, the item type must 
        ## be added to the parameters
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
        # Url setup
        base_url = f'{settings.base_url}/{settings.search_route}{params}'
        # Perform request, including pagination
        final_result = {}
        final_result['base_url'] = base_url
        result = []
        req = 1
        has_more = True
        url = f'{base_url}&page={req}'
        while has_more:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                result.extend(data['items'])
                has_more = data['has_more']
                req += 1
                url = f'{base_url}&page={req}'
            else:
                msg = f'API call failed with status code: {resp.status_code}'
                raise Exception(msg)
        final_result['result'] = result
        return final_result

    
    def get_multi(
        self, 
        api_key: str, 
        settings: Settings, 
        fields: Optional[ List[str] ] = None, 
        order_by: Optional[str] = None,
        order_dir: Optional[str] = None
    ) -> List[ Dict[Any,Any] | None ]:
        """Get a list of all items
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
        # Perform request, including pagination
        result = []
        req = 1
        has_more = True
        url = f'{base_url}&page={req}'
        while has_more:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                result.extend(data['items'])
                has_more = data['has_more']
                req += 1
                url = f'{base_url}&page={req}'
            else:
                msg = f'API call failed with status code: {resp.status_code}'
                raise Exception(msg)
        return result


    def get(
        self, 
        api_key: str, 
        settings: Settings, 
        id: str,
        fields: Optional[ List[str] ] = None
    ) -> Dict[str,Any]:
        """Get a note by ID
        """
        # Setup request parameters
        ## Default params
        params = f'?token={api_key}'
        ## Optional params
        if fields:
            fieldnames = self.fields_to_params(fields)
            params += f'&fields={fieldnames}'
        # Url setup
        url = f'{settings.base_url}/{self.route}/{id}{params}'
        resp = requests.get(url)
        return resp.json()
    

    def create(
        self, 
        api_key: str, 
        settings: Settings, 
        data: Dict[str, Any] | str
    ) -> Dict[str, Any] | List[Any]:
        """POST a new entity to the api. 
        WARNING: data validation is left to inherited implementation
        """
        # Make sure minimum fields are present in data
        # TODO: below is not clear if it is for notes or also for other entities.
        ## Notes need a dict with fields as payload. Other entities can often 
        ## be created with just their name in string.
        for field in self.fields_create_required:
            if not field in data.keys():
                return {'error': f'Required field {field} was not found in data.'}
        # Setup request parameters
        params = f'?token={api_key}'
        # Setup url
        url = f'{settings.base_url}/{self.route}{params}'
        # Perform request
        resp = requests.post(url, json=data)
        return resp.json()



class Note(Item):
    """Interact with notes in Joplin via the webclipper API
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



class Tag(Item):
    """Interact with tags in Joplin via the webclipper API
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
    ) -> Any:
        """Add this tag to a note"""
        # Setup request parameters
        params = f'?token={api_key}'
        # Setup URL
        url = f'{settings.base_url}/{self.route}/{tag_id}/notes{params}'
        # Setup request payload
        data = {'id': note_id}
        # Perform request
        resp = requests.post(url, json=data)
        return resp.json()



class Folder(Item):
    """Interact with folders (notebooks) in Joplin via the webclipper API
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



class Revision(Item):
    """Interact with Revisions in Joplin via the webclipper API
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
