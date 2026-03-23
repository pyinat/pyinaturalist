"""Data models that represent iNaturalist API response objects.
See :ref:`data-models` section for usage details.
"""

# ruff: noqa: F401, E402
# isort: skip_file
from datetime import datetime, timezone
from typing import TypeAlias
from collections.abc import Callable, Iterable

import attr
from attr import define, validators

from pyinaturalist.constants import JsonResponse, ResponseOrResults
from pyinaturalist.converters import convert_lat_long, try_datetime
from pyinaturalist.models.base import BaseModel, BaseModelCollection, T, load_json
from pyinaturalist.models.field_path import (
    FieldDescriptor,
    FieldPath,
    FieldProxy,
    build_fields_dict,
)
from pyinaturalist.models.lazy_property import LazyProperty, add_lazy_attrs, get_lazy_properties


# Aliases and minor helper functions used by model classes
# --------------------------------------------------------

define_model: Callable = define(auto_attribs=False, field_transformer=add_lazy_attrs)
define_model_custom_init: Callable = define(
    auto_attribs=False, init=False, field_transformer=add_lazy_attrs
)
define_model_collection: Callable = define(auto_attribs=False, order=False, slots=False)


def _install_field_descriptors_on(cls: type) -> None:
    """Install :class:`.FieldDescriptor` on each public attrs field of ``cls``.

    Only processes slots defined directly on ``cls`` (not inherited), to avoid interfering with
    attrs' slot-inheritance mechanism when child classes redefine a field.

    Must be called AFTER all model subclasses are defined, so attrs has finished building all
    classes and will no longer inspect parent slot descriptors via ``getattr``.
    """
    for f in attr.fields(cls):
        public_name = f.name.lstrip('_')
        if f.name.startswith('_') or not f.init:
            continue
        slot_desc = cls.__dict__.get(public_name)
        if slot_desc is None:
            continue
        if isinstance(slot_desc, (LazyProperty, FieldDescriptor)):
            continue
        if type(slot_desc).__name__ == 'member_descriptor':
            setattr(cls, public_name, FieldDescriptor(public_name, slot_desc))


def field(doc: str = '', options: Iterable | None = None, metadata: dict | None = None, **kwargs):
    """A field with extra metadata for documentation and options"""
    metadata = metadata or {}
    metadata['doc'] = doc
    metadata['options'] = options
    return attr.field(**kwargs, metadata=metadata)


# TODO: Case-insensitive version
def is_in(options: Iterable):
    """Validator for an optional multiple-choice attribute"""
    return validators.in_(list(options) + [None])


def coordinate_pair(doc: str | None = None, **kwargs):
    """Field containing a pair of coordinates"""
    return field(
        default=None,
        converter=convert_lat_long,
        doc=doc or 'Location in ``(latitude, longitude)`` decimal degrees',
        **kwargs,
    )


def datetime_field(**kwargs):
    """Field that converts date/time strings into datetime objects"""
    return field(default=None, converter=try_datetime, **kwargs)


def datetime_now_field(**kwargs):
    """Field that converts date/time strings into datetime objects, and defaults to the current time"""
    return field(converter=try_datetime, factory=lambda: datetime.now(timezone.utc), **kwargs)


def upper(value) -> str | None:
    """Converter to change a string to uppercase, if applicable"""
    return value.upper() if isinstance(value, str) else None


# Models imported in order of dependencies
# --------------------------------------------------------

from pyinaturalist.models.media import IconPhoto, Photo, Sound
from pyinaturalist.models.place import Place
from pyinaturalist.models.user import User, UserCount, UserCounts
from pyinaturalist.models.checklist import Checklist, EstablishmentMeans, ListedTaxon
from pyinaturalist.models.conservation_status import ConservationStatus, TaxonSummary
from pyinaturalist.models.taxon import Taxon, TaxonCount, TaxonCounts, LifeList, make_tree
from pyinaturalist.models.controlled_term import (
    Annotation,
    ControlledTerm,
    ControlledTermCount,
    ControlledTermCounts,
    ControlledTermValue,
)
from pyinaturalist.models.identification import Comment, Identification
from pyinaturalist.models.message import Message
from pyinaturalist.models.observation_field import ObservationField, ObservationFieldValue
from pyinaturalist.models.project import (
    Project,
    ProjectObservation,
    ProjectObservationField,
    ProjectUser,
)
from pyinaturalist.models.observation import (
    Observation,
    Observations,
    Application,
    Fave,
    Flag,
    HistogramBin,
    Histogram,
    QualityMetric,
    Vote,
)
from pyinaturalist.models.search import SearchResult


# Type aliases involving model objects
ModelObjects: TypeAlias = BaseModel | BaseModelCollection | Iterable[BaseModel]
ResponseOrObject: TypeAlias = BaseModel | JsonResponse
ResponseOrObjects: TypeAlias = ModelObjects | ResponseOrResults

# Short aliases for some of the longer class names
ID = Identification
OFD = ObservationField
OFV = ObservationFieldValue

# Install FieldDescriptors on all model classes so that class-level attribute access returns
# FieldPath objects for typed field selection. This MUST run after all model classes have been
# imported and fully built by attrs, to avoid interfering with attrs' slot-inheritance logic.
for _cls in [
    BaseModel,
    IconPhoto,
    Photo,
    Sound,
    Place,
    User,
    UserCount,
    Checklist,
    EstablishmentMeans,
    ListedTaxon,
    ConservationStatus,
    TaxonSummary,
    Taxon,
    TaxonCount,
    Annotation,
    ControlledTerm,
    ControlledTermCount,
    ControlledTermValue,
    Comment,
    Identification,
    Message,
    ObservationField,
    ObservationFieldValue,
    Project,
    ProjectObservation,
    ProjectObservationField,
    ProjectUser,
    Observation,
    Application,
    Fave,
    Flag,
    QualityMetric,
    Vote,
    SearchResult,
]:
    _install_field_descriptors_on(_cls)
del _cls
