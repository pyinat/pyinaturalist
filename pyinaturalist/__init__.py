from os import getenv

# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY  # noqa

# Set the pre-release version number, if set by CI job
__version__ = '0.13.0'
__version__ += getenv('PRE_RELEASE_SUFFIX', '')

DEFAULT_USER_AGENT = f'pyinaturalist/{__version__}'
user_agent = DEFAULT_USER_AGENT
