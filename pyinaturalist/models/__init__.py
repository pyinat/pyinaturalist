"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401
# TODO: Validators for multiple choice fields?
from typing import Callable
from attr import define

from pyinaturalist.models.base import (
    ModelObjects,
    ResponseOrObject,
    ResponseOrObjects,
    BaseModel,
    BaseModelCollection,
    datetime_attr,
    datetime_now_attr,
    coordinate_pair,
    kwarg,
    load_json,
)
from pyinaturalist.models.lazy_property import LazyProperty, add_lazy_attrs, get_model_fields

# attrs class decorator with the most commonly used options
define_model: Callable = define(auto_attribs=False, field_transformer=add_lazy_attrs)

# Imported in order of model dependencies
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon, TaxonCount, TaxonCounts
from pyinaturalist.models.user import User
from pyinaturalist.models.controlled_term import Annotation, ControlledTerm, ControlledTermValue
from pyinaturalist.models.comment import Comment
from pyinaturalist.models.identification import Identification
from pyinaturalist.models.life_list import LifeList, LifeListTaxon
from pyinaturalist.models.place import Place
from pyinaturalist.models.project import (
    Project,
    ProjectObservation,
    ProjectObservationField,
    ProjectUser,
)
from pyinaturalist.models.observation_field import ObservationField, ObservationFieldValue
from pyinaturalist.models.observation import Observation
from pyinaturalist.models.search import SearchResult


# Add aliases for some of the longer class names
ID = Identification
OFD = ObservationField
OFV = ObservationFieldValue
