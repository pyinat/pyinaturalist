"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401
# Imported in order of dependencies

# TODO: Fix mypy "unsupported converter false positives
# TODO: Add formatters as model methods
# TODO: Unit tests. So many unit tests.
# TODO: Model for Observation Fields?
from pyinaturalist.models.base import (
    BaseModel,
    datetime_attr,
    datetime_now_attr,
    coordinate_pair,
    kwarg,
)
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon
from pyinaturalist.models.user import User, ProjectUser
from pyinaturalist.models.place import Place
from pyinaturalist.models.project import Project
from pyinaturalist.models.identification import Identification
from pyinaturalist.models.observation import Observation
