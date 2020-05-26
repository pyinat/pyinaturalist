import logging

__author__ = "Nicolas Noé"
__email__ = "nicolas@niconoe.eu"
__version__ = "0.9.0"

DEFAULT_USER_AGENT = "Pyinaturalist/{version}".format(version=__version__)

user_agent = DEFAULT_USER_AGENT

# Enable logging for urllib and other external loggers
logging.basicConfig(level="DEBUG")
