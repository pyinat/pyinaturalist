# flake8: noqa: F401, F403
from os import getenv

# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY  # noqa

# Set the pre-release version number, if set by CI job
__version__ = '0.13.0'
__version__ += getenv('PRE_RELEASE_SUFFIX', '')

DEFAULT_USER_AGENT = f'pyinaturalist/{__version__}'
user_agent = DEFAULT_USER_AGENT

# Ignore ImportErrors if this is imported outside a virtualenv
try:
    from pyinaturalist.auth import get_access_token
    from pyinaturalist.formatters import *
    from pyinaturalist.rest_api import *
    from pyinaturalist.node_api import *
except ImportError as e:
    print(e)
