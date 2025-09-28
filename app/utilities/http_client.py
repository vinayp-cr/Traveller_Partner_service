import requests
from app.core.config import settings

def post_request(url: str, headers: dict, payload: dict, timeout: float = None):
    """Make a POST request with configurable headers and timeout"""
    timeout = timeout or settings.DEFAULT_TIMEOUT
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    return response

def get_request(url: str, headers: dict, params: dict = None, timeout: float = None):
    """Make a GET request with configurable headers and timeout"""
    timeout = timeout or settings.DEFAULT_TIMEOUT
    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    return response

def make_request(method: str, url: str, headers: dict, **kwargs):
    """Generic request method with configurable headers"""
    timeout = kwargs.get('timeout', settings.DEFAULT_TIMEOUT)
    kwargs['timeout'] = timeout
    
    if method.upper() == 'POST':
        return requests.post(url, headers=headers, **kwargs)
    elif method.upper() == 'GET':
        return requests.get(url, headers=headers, **kwargs)
    elif method.upper() == 'PUT':
        return requests.put(url, headers=headers, **kwargs)
    elif method.upper() == 'DELETE':
        return requests.delete(url, headers=headers, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
