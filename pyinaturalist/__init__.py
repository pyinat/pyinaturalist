# flake8: noqa: F401, F403
__version__ = '0.15.0'
DEFAULT_USER_AGENT: str = f'pyinaturalist/{__version__}'
user_agent = DEFAULT_USER_AGENT

# Ignore ImportErrors if this is imported outside a virtualenv
try:
    from pyinaturalist.auth import get_access_token
    from pyinaturalist.client import iNatClient
    from pyinaturalist.constants import *
    from pyinaturalist.formatters import enable_logging, format_table, pprint
    from pyinaturalist.models import *
    from pyinaturalist.v0 import *
    from pyinaturalist.v1 import *
    from pyinaturalist.v2 import *

    # For disambiguation
    from pyinaturalist.v0 import get_observations as get_observations_v0
    from pyinaturalist.v0 import create_observation as create_observation_v0
except ImportError as e:
    print(e)
