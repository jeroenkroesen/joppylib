"""Helper functions to connect to the Joplin webclipper API
"""

import time

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
        resp = requests.get(url_ping, timeout=(3, 5))
        return resp.ok
    except requests.exceptions.RequestException:
        return False



def get_auth_token(
    base_url: str = 'http://localhost:41184',
    route_init: str = 'auth',
    route_check: str = 'auth/check',
    poll_interval: float = 1.0,
    poll_timeout: float = 120.0
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
    resp_init = requests.post(url_init, timeout=(3, 5))
    init_token = resp_init.json()['auth_token']
    # Check if the user has responded and return in case of result
    url_check = f'{base_url}/{route_check}?auth_token={init_token}'
    deadline = time.monotonic() + poll_timeout
    while time.monotonic() < deadline:
        resp_check = requests.get(url_check, timeout=(3, 5))
        data_check = resp_check.json()
        if data_check['status'] != 'waiting':
            return data_check
        time.sleep(poll_interval)
    raise TimeoutError(
        f'No response to auth request within {poll_timeout} seconds'
    )
