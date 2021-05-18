"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401
# Imported in order of dependencies
# TODO: Model for Projects
# TODO: Model for Comments?
# TODO: Model for Observation Fields?
from pyinaturalist.models.base import (
    BaseModel,
    aliased_kwarg,
    created_timestamp,
    kwarg,
    timestamp,
)
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon
from pyinaturalist.models.user import User
from pyinaturalist.models.identification import Identification
from pyinaturalist.models.observation import Observation
