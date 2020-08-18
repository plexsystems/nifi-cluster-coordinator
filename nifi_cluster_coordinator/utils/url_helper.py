import urllib.parse as urlparse
from typing import List, Dict


def construct_path_parts(parts: List[str]) -> str:
    """Return a string separated by '/' for a url path."""
    if isinstance(parts, list):
        return '/'.join(parts)
    elif parts is None:
        return ''
    else:
        return parts


def construct_query_parts(parts: Dict[str, str]) -> str:
    """Return a query string constrcuted from key value pairs"""
    if isinstance(parts, dict):
        return '&'.join(x + '=' + y for x, y in parts.items())
    else:
        return parts


def construct_api_url(scheme: str,
                      host_name: str,
                      path_parts: List[str] = None,
                      query_parts: Dict[str, str] = None) -> str:
    return urlparse.urlunsplit((
        scheme,
        host_name,
        construct_path_parts(path_parts),
        construct_query_parts(query_parts),
        None
    ))
