import pyinaturalist


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
