"""
Functions to access the original (v0) iNaturalist API
See: https://www.inaturalist.org/pages/api+reference
"""
# flake8: noqa: F401, F403

from pyinaturalist.v0.observation_fields import get_observation_fields, put_observation_field_values
from pyinaturalist.v0.observations import (
    create_observation,
    delete_observation,
    get_observations,
    update_observation,
    upload_photos,
    upload_sounds,
)
