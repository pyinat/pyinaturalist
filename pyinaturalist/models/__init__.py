"""Data models that represent iNaturalist API response objects.
See :ref:`user_guide:models` section for usage details.
"""
# flake8: noqa: F401
# isort: skip_file
from datetime import datetime, timezone
from typing import Callable, Dict, Iterable, Optional, Union

import attr
from attr import define, validators

from pyinaturalist.constants import JsonResponse, ResponseOrResults
from pyinaturalist.converters import convert_lat_long, try_datetime
from pyinaturalist.models.base import BaseModel, BaseModelCollection, T, load_json
from pyinaturalist.models.lazy_property import LazyProperty, add_lazy_attrs, get_lazy_properties


# Aliases and minor helper functions used by model classes
# --------------------------------------------------------

# Attrs class decorators with the most commonly used options
define_model: Callable = define(auto_attribs=False, field_transformer=add_lazy_attrs)
define_model_collection: Callable = define(auto_attribs=False, order=False, slots=False)


def field(
    doc: str = '', options: Optional[Iterable] = None, metadata: Optional[Dict] = None, **kwargs
):
    """A field with extra metadata for documentation and options"""
    metadata = metadata or {}
    metadata['doc'] = doc
    metadata['options'] = options
    return attr.field(**kwargs, metadata=metadata)


# TODO: Case-insensitive version
def is_in(options: Iterable):
    """Validator for an optional multiple-choice attribute"""
    return validators.in_(list(options) + [None])


def coordinate_pair(doc: Optional[str] = None, **kwargs):
    """Field containing a pair of coordiantes"""
    return field(
        default=None,
        converter=convert_lat_long,
        doc=doc or 'Location in ``(latitude, logitude)`` decimal degrees',
        **kwargs,
    )


def datetime_field(**kwargs):
    """Field that converts date/time strings into datetime objects"""
    return field(default=None, converter=try_datetime, **kwargs)


def datetime_now_field(**kwargs):
    """Field that converts date/time strings into datetime objects, and defaults to the current time"""
    return field(converter=try_datetime, factory=lambda: datetime.now(timezone.utc), **kwargs)


def upper(value) -> Optional[str]:
    """Converter to change a string to uppercase, if applicable"""
    return value.upper() if isinstance(value, str) else None


# Models imported in order of dependencies
# --------------------------------------------------------

from pyinaturalist.models.photo import IconPhoto, Photo
from pyinaturalist.models.place import Place
from pyinaturalist.models.user import User, UserCount, UserCounts
from pyinaturalist.models.taxon_meta import (
    ConservationStatus,
    EstablishmentMeans,
    ListedTaxon,
    TaxonSummary,
)
from pyinaturalist.models.taxon import Taxon, TaxonCount, TaxonCounts
from pyinaturalist.models.controlled_term import (
    Annotation,
    ControlledTerm,
    ControlledTermCount,
    ControlledTermCounts,
    ControlledTermValue,
)
from pyinaturalist.models.identification import Comment, Identification
from pyinaturalist.models.life_list import LifeList, LifeListTaxon
from pyinaturalist.models.message import Message
from pyinaturalist.models.observation_field import ObservationField, ObservationFieldValue
from pyinaturalist.models.project import (
    Project,
    ProjectObservation,
    ProjectObservationField,
    ProjectUser,
)
from pyinaturalist.models.observation import Observation, Observations
from pyinaturalist.models.search import SearchResult


# Type aliases involving model objects
ModelObjects = Union[BaseModel, BaseModelCollection, Iterable[BaseModel]]
ResponseOrObject = Union[BaseModel, JsonResponse]
ResponseOrObjects = Union[ModelObjects, ResponseOrResults]

# Short aliases for some of the longer class names
ID = Identification
OFD = ObservationField
OFV = ObservationFieldValue
