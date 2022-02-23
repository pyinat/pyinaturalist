"""Utilities for generating documentation for model classes. This outputs CSV files that are then
rendered in the docs as tables.
"""
import csv
from inspect import getmembers, isclass
from os import makedirs
from os.path import join
from typing import TYPE_CHECKING, Any, List, Tuple, Type, get_type_hints

from attr import Attribute
from sphinx.config import Config
from sphinx_autodoc_typehints import format_annotation

from pyinaturalist.constants import DOCS_DIR
from pyinaturalist.models import LazyProperty, get_lazy_properties

IGNORE_PROPERTIES = ['row']
MODEL_DOC_DIR = join(DOCS_DIR, 'models')


def document_models(app):
    """Export attribute documentation for all models to CSV files"""
    makedirs(MODEL_DOC_DIR, exist_ok=True)
    for model in get_model_classes():
        doc_table = get_model_doc(model, app.config)
        export_model_doc(model.__name__, doc_table)


def get_model_classes() -> List[Type]:
    """Get all model classes defined in the :py:mod:`pyinaturalist.models` package"""
    import pyinaturalist.models
    from pyinaturalist.models import BaseModel

    model_classes = []
    for _, obj in getmembers(pyinaturalist.models):
        if isclass(obj) and issubclass(obj, BaseModel):
            model_classes.append(obj)
    return model_classes


def get_model_doc(cls: Type, config: Config) -> List[Tuple[str, str, str]]:
    """Get the name, type and description for all model attributes, properties, and LazyProperties.
    If an attribute has metadata for options (possible values for the attribute), include those
    options in the description.
    """
    # Used internally by sphinx-autodoc-typehints
    config._annotation_globals = getattr(cls, "__globals__", {})

    doc_rows = [
        _get_field_doc(field, config)
        for field in cls.__attrs_attrs__
        if not field.name.startswith('_')
    ]
    doc_rows += [('', '', '')]
    doc_rows += [_get_property_doc(prop, config) for prop in get_properties(cls)]
    doc_rows += [('', '', '')]
    doc_rows += [
        _get_lazy_property_doc(prop, config) for _, prop in get_lazy_properties(cls).items()
    ]

    delattr(config, "_annotation_globals")
    return doc_rows


def get_properties(cls: Type) -> List[property]:
    """Get all @property descriptors from a class"""
    return [
        member
        for member in cls.__dict__.values()
        if isinstance(member, property)
        and not isinstance(member, LazyProperty)
        and member.fget.__name__ not in IGNORE_PROPERTIES  # type: ignore
    ]


def _get_field_doc(field: Attribute, config: Config) -> Tuple[str, str, str]:
    """Get a row documenting an attrs Attribute"""
    rtype = format_annotation(field.type, config)
    doc = field.metadata.get('doc', '')
    options = field.metadata.get('options', [])
    if options:
        options = ', '.join([f'``{opt}``' for opt in options if opt])
        doc += f'\n\n**Options:** {options}'
    return (f'**{field.name}**', rtype, doc)


def _get_property_doc(prop: property, config: Config) -> Tuple[str, str, str]:
    """Get a row documenting a regular @property"""
    fget_rtype = get_type_hints(prop.fget).get('return', Any)
    rtype = format_annotation(fget_rtype, config)
    if TYPE_CHECKING:
        assert prop.fget is not None

    doc = (prop.fget.__doc__ or '').split('\n')[0]
    property_type = format_annotation(property, config)
    return (f'**{prop.fget.__name__}** ({property_type})', rtype, doc)


def _get_lazy_property_doc(prop: LazyProperty, config: Config) -> Tuple[str, str, str]:
    """Get a row documenting a LazyProperty"""
    rtype = format_annotation(prop.type, config)

    lazy_property_type = format_annotation(LazyProperty, config)
    return (f'**{prop.__name__}** ({lazy_property_type})', rtype, prop.__doc__ or '')


def export_model_doc(model_name, doc_table):
    """Export attribute documentation for a model to a CSV file"""
    with open(join(MODEL_DOC_DIR, f'{model_name}.csv'), 'w') as f:
        csv.writer(f).writerows(doc_table)
