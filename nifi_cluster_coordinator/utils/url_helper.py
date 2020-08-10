from typing import List, Dict


def construct_path_parts(parts: List[str]) -> str:
    """Return a string separated by '/' for a url path."""
    if parts is None:
        return ''
    if isinstance(parts, list):
        return '/'.join(parts)
    return parts


def construct_query_parts(parts: Dict[str, str]) -> str:
    """Return a query string constrcuted from key value pairs"""
    if parts is None:
        return None
    if isinstance(parts, dict):
        return '&'.join(x + '=' + y for x, y in parts.items())
    return parts
