from logging import getLogger
from os import getenv

__author__ = "Nicolas Noé"
__email__ = "nicolas@niconoe.eu"
__version__ = "0.12.0"

# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY

DEFAULT_USER_AGENT = f"pyinaturalist/{__version__}"
user_agent = DEFAULT_USER_AGENT


def get_prerelease_version(version: str) -> str:
    """If we're running in a GitHub Action job on the dev branch, get a prerelease version using the
    current build number. For example: ``1.0.0 -> 1.0.0-dev.123``
    """
    if getenv("GITHUB_REF") == "refs/heads/dev":
        build_number = getenv("GITHUB_RUN_NUMBER", "0")
        version = f"{version}.dev{build_number}"
        getLogger(__name__).info(f"Using pre-release version: {version}")
    return version


# This won't modify the version outside of a GitHub Action
__version__ = get_prerelease_version(__version__)
