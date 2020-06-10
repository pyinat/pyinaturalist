from logging import getLogger
from os import getenv

__author__ = "Nicolas Noé"
__email__ = "nicolas@niconoe.eu"
__version__ = "0.10.0"

# These are imported here so they can be set with pyinaturalist.<variable>
from pyinaturalist.constants import DRY_RUN_ENABLED, DRY_RUN_WRITE_ONLY

DEFAULT_USER_AGENT = "Pyinaturalist/{version}".format(version=__version__)
user_agent = DEFAULT_USER_AGENT


def get_prerelease_version(version: str) -> str:
    """ If we're running in a Travis CI job on the dev branch, get a prerelease version using the
    current build number. For example: ``1.0.0 -> 1.0.0-dev.123``

    This could also be done in ``.travis.yml``, but it's a bit cleaner to do in python, and
    ``semantic_version`` provides some extra sanity checks.
    """
    if not (getenv("TRAVIS") == "true" and getenv("TRAVIS_BRANCH") == "dev"):
        return version
    # If we happen to be in a dev build, this will prevent the initial 'pip install' from failing
    try:
        from semantic_version import Version
    except ImportError:
        return version

    new_version = Version(version)
    new_version.prerelease = ("dev", getenv("TRAVIS_BUILD_NUMBER", "0"))
    getLogger(__name__).info("Using pre-release version: {}".format(new_version))
    return str(new_version)


# This won't modify the version outside of Travis
__version__ = get_prerelease_version(__version__)
