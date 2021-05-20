"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401

# TODO: Add formatters as model methods
# TODO: Unit tests. So many unit tests.
from pyinaturalist.models.base import (
    BaseModel,
    dataclass,
    datetime_attr,
    datetime_now_attr,
    coordinate_pair,
    kwarg,
)

# Imported in order of model dependencies
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon
from pyinaturalist.models.user import User, ProjectUser
from pyinaturalist.models.comment import Comment
from pyinaturalist.models.identification import ID, Identification
from pyinaturalist.models.place import Place
from pyinaturalist.models.project import Project
from pyinaturalist.models.observation_field import OF, OFV, ObservationField, ObservationFieldValue
from pyinaturalist.models.observation import Observation
