"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401
# Imported in order of dependencies
from pyinaturalist.models.base import (
    BaseModel,
    ModelCollection,
    aliased_kwarg,
    created_timestamp,
    kwarg,
    timestamp,
)
from pyinaturalist.models.photo import Photo, Photos
from pyinaturalist.models.taxon import Taxon, Taxa
from pyinaturalist.models.user import User
from pyinaturalist.models.identification import Identification, Identifications
from pyinaturalist.models.observation import Observation, Observations
