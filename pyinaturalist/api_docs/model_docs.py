"""Utilities for generating documentation for model classes. This outputs CSV files that are then
rendered in the docs as rST tables.
"""
import csv
from inspect import getmembers, isclass
from os import makedirs
from os.path import join
from typing import Any, List, Tuple, Type, get_type_hints

from attr import Attribute
from sphinx_autodoc_typehints import format_annotation

from pyinaturalist.constants import DOCS_DIR
from pyinaturalist.models import LazyProperty, get_lazy_properties

IGNORE_PROPERTIES = ['row']
MODEL_DOC_DIR = join(DOCS_DIR, 'models')
PROPERTY_TYPE = format_annotation(property)
LAZY_PROPERTY_TYPE = format_annotation(LazyProperty)


def document_models(app):
    """Export attribute documentation for all models to CSV files"""
    makedirs(MODEL_DOC_DIR, exist_ok=True)
    for model in get_model_classes():
        doc_table = get_model_doc(model)
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


# TODO: Also include regular @properties?
# TODO: CSS to style LazyProperties with a different background color?
# TODO: Remove autodoc member docs for LazyProperties
def get_model_doc(cls: Type) -> List[Tuple[str, str, str]]:
    """Get the name, type and description for all model attributes, properties, and LazyProperties.
    If an attribute has metadata for options (possible values for the attribute), include those
    options in the description.
    """

    doc_rows = [_get_field_doc(field) for field in cls.__attrs_attrs__ if not field.name.startswith('_')]
    doc_rows += [('', '', '')]
    doc_rows += [_get_property_doc(prop) for prop in get_properties(cls)]
    doc_rows += [('', '', '')]
    doc_rows += [_get_lazy_property_doc(prop) for _, prop in get_lazy_properties(cls).items()]
    return doc_rows


def get_properties(cls: Type) -> List[property]:
    """Get all @property descriptors from a class"""
    return [
        member
        for member in cls.__dict__.values()
        if isinstance(member, property)
        and not isinstance(member, LazyProperty)
        and member.fget.__name__ not in IGNORE_PROPERTIES
    ]


def _get_field_doc(field: Attribute) -> Tuple[str, str, str]:
    """Get a row documenting an attrs Attribute"""
    rtype = format_annotation(field.type)
    doc = field.metadata.get('doc', '')
    options = field.metadata.get('options', [])
    if options:
        options = ', '.join([f'``{opt}``' for opt in filter(None, options)])
        doc += f'\n\n**Options:** {options}'
    return (f'**{field.name}**', rtype, doc)


def _get_property_doc(prop: property) -> Tuple[str, str, str]:
    """Get a row documenting a regular @property"""
    fget_rtype = get_type_hints(prop.fget).get('return', Any)
    rtype = format_annotation(fget_rtype)
    doc = (prop.fget.__doc__ or '').split('\n')[0]
    return (f'**{prop.fget.__name__}** ({PROPERTY_TYPE})', rtype, doc)


def _get_lazy_property_doc(prop: LazyProperty) -> Tuple[str, str, str]:
    """Get a row documenting a LazyProperty"""
    rtype = format_annotation(prop.type)
    return (f'**{prop.__name__}** ({LAZY_PROPERTY_TYPE})', rtype, prop.__doc__)


def export_model_doc(model_name, doc_table):
    """Export attribute documentation for a model to a CSV file"""
    with open(join(MODEL_DOC_DIR, f'{model_name}.csv'), 'w') as f:
        csv.writer(f).writerows(doc_table)
