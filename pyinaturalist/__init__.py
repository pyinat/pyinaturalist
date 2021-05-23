# flake8: noqa: F401, F403
# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY  # noqa

__version__ = '0.14.0'
DEFAULT_USER_AGENT = f'pyinaturalist/{__version__}'
user_agent = DEFAULT_USER_AGENT

# Ignore ImportErrors if this is imported outside a virtualenv
try:
    from pyinaturalist.auth import get_access_token
    from pyinaturalist.formatters import *
    from pyinaturalist.models import *
    from pyinaturalist.v0 import *
    from pyinaturalist.v1 import *
    from pyinaturalist.v2 import *

    # For disambiguation
    from pyinaturalist.v0 import get_observations as get_observations_v0
    from pyinaturalist.v1 import get_observations as get_observations_v1
except ImportError as e:
    print(e)
