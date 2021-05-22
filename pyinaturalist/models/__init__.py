"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401

# TODO: Add formatters as model methods
# TODO: Add nested model objects to __repr__ methods
# TODO: Validators for multiple choice fields?
from pyinaturalist.models.base import (
    BaseModel,
    datetime_attr,
    datetime_now_attr,
    cached_model_property,
    cached_property,
    coordinate_pair,
    kwarg,
)

# Imported in order of model dependencies
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon
from pyinaturalist.models.user import User
from pyinaturalist.models.comment import Comment
from pyinaturalist.models.identification import ID, Identification
from pyinaturalist.models.place import Place
from pyinaturalist.models.project import Project, ProjectObservationField, POF, ProjectUser
from pyinaturalist.models.observation_field import ObservationField, OF, ObservationFieldValue, OFV
from pyinaturalist.models.observation import Observation
