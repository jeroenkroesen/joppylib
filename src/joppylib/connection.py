"""Helper functions to connect to the Joplin webclipper API
"""

import requests


def check_connection(
    base_url: str = 'http://localhost:41184', 
    route_ping: str = 'ping'
) -> bool:
    """Check if there is connectivity with the webclipper service

    Parameters
    ----------
    base_url : str
        A string representing the full address of the joping API.
        It consists of the parts: {protocol}{host}:{port}.
        The current default is "http://localhost:41184"
    route_ping: str
        The API route for the connection ping.
        The current default is "ping"

    Returns
    -------
    bool
        True if the Joplin DataApi responds to a GET request.
        False if there is no connection detected
    """
    url_ping = f'{base_url}/{route_ping}'
    try:
        requests.get(url_ping)
        return True
    except requests.exceptions.ConnectionError:
        return False



def get_auth_token(
    base_url: str = 'http://localhost:41184', 
    route_init: str = 'auth', 
    route_check: str = 'auth/check'
) -> dict:
    """Attempt to get an API auth token interactively

    Parameters
    ----------
    base_url : str
        A string representing the full address of the joping API.
        It consists of the parts: {protocol}{host}:{port}.
        The current default is "http://localhost:41184"
    route_init : str
        The API route to request an api token
        The current default is "auth"
    route_check : str
        The API route to check if the user has authorized us and given out 
        a token.
        The current default is "auth/check"

    Returns
    -------
    dict
        A dictionary with information about the user response and if the 
        response was positive: an auth key.
        If the key "status" has a value of "accepted" the auth token can be 
        found in the key "token". 
        If "status" has any other value, the authorization failed. 
        Possibly, the dict can be examined to determine the reason of failure.
    """
    # Initiate the auth process
    # User will be presented popup in Joplin to allow access
    # init_token allows checking the status
    url_init = f'{base_url}/{route_init}'
    resp_init = requests.post(url_init)
    init_token = resp_init.json()['auth_token']
    # Check if the user has responded and return in case of result
    url_check = f'{base_url}/{route_check}?auth_token={init_token}'
    while True:
        resp_check = requests.get(url_check)
        data_check = resp_check.json()
        if data_check['status'] != 'waiting':
            return data_check
