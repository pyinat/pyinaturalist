"""Dataclasses for modeling iNaturalist API response objects"""
# flake8: noqa: F401
# TODO: Add formatters as model methods
# TODO: Validators for multiple choice fields?
from typing import Callable
from attr import define

from pyinaturalist.models.base import (
    BaseModel,
    datetime_attr,
    datetime_now_attr,
    coordinate_pair,
    get_model_fields,
    kwarg,
    load_json,
    make_attribute,
)
from pyinaturalist.models.lazy_property import LazyProperty, add_lazy_attrs

# attrs class decorator with the most commonly used options
define_model: Callable = define(auto_attribs=False, field_transformer=add_lazy_attrs)

# Imported in order of model dependencies
from pyinaturalist.models.photo import Photo
from pyinaturalist.models.taxon import Taxon
from pyinaturalist.models.user import User
from pyinaturalist.models.annotation import Annotation
from pyinaturalist.models.comment import Comment
from pyinaturalist.models.identification import Identification
from pyinaturalist.models.life_list import LifeList, LifeListTaxon
from pyinaturalist.models.place import Place
from pyinaturalist.models.project import Project, ProjectObservationField, ProjectUser
from pyinaturalist.models.observation_field import ObservationField, ObservationFieldValue
from pyinaturalist.models.observation import Observation


# Add aliases for some of the longer class names
ID = Identification
OF = ObservationField
OFV = ObservationFieldValue
POF = ProjectObservationField


# If rich is installed, update its pretty-printer to include model @properties. Since this is only
# cosmetic, it's not a big deal, but it would be preferable to do this without monkey-patching.
try:
    from rich import pretty

    pretty._get_attr_fields = get_model_fields
    pretty.install()
except ImportError:
    pass
