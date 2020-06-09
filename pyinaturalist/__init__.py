import logging

__author__ = "Nicolas Noé"
__email__ = "nicolas@niconoe.eu"
__version__ = "0.9.1"

DEFAULT_USER_AGENT = "Pyinaturalist/{version}".format(version=__version__)
user_agent = DEFAULT_USER_AGENT

# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY

# Enable logging for urllib and other external loggers
logging.basicConfig(level="DEBUG")
