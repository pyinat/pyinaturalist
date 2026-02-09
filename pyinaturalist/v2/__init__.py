"""
Functions to access the iNaturalist API v2
See: http://api.inaturalist.org/v2/docs/
"""

# ruff: noqa: F401, F403
from pyinaturalist.v2.observations import (
    create_observation,
    delete_observation,
    get_observations,
    set_observation_field,
    update_observation,
    upload,
)
