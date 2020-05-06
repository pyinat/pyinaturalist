import pyinaturalist
from typing import Dict, Any


# For Python < 3.5 compatibility
def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_user_agent(user_agent: str = None) -> str:
    """Return the user agent to be used."""
    if user_agent is not None:  # If we explicitly provide one, use it
        return user_agent
    else:  # Otherwise we have a global one in __init__.py (configurable, with sensible defaults)
        return pyinaturalist.user_agent


def concat_list_params(params) -> Dict[str, Any]:
    """Convert any list parameters into an API-compatible (comma-delimited) string.
    Will be url-encoded by requests. For example: `['k1', 'k2', 'k3'] -> k1%2Ck2%2Ck3`
    """
    for k, v in params.items():
        if isinstance(v, list):
            params[k] = ",".join(v)
    return params


def strip_empty_params(params) -> Dict[str, Any]:
    """Remove any request parameters with empty or ``None`` values."""
    return {k: v for k, v in params.items() if v}
