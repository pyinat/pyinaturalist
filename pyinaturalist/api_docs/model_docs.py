"""Utilities for generating documentation for model classes. This outputs CSV files that are then
rendered in the docs as rST tables.
"""
import csv
from inspect import getmembers, isclass
from os import makedirs
from os.path import join
from typing import List, Tuple, Type

from attr import Attribute

from pyinaturalist.constants import DOCS_DIR

MODEL_DOC_DIR = join(DOCS_DIR, 'models')


def document_models(app):
    """Export attribute documentation for all models to CSV files"""
    makedirs(MODEL_DOC_DIR, exist_ok=True)
    for model in get_model_classes():
        doc_table = get_model_doc(model)
        export_model_doc(model.__name__, doc_table)


def get_model_classes() -> List[Type['BaseModel']]:
    """Get all model classes defined in the :py:mod:`pyinaturalist.models` package"""
    import pyinaturalist.models
    from pyinaturalist.models import BaseModel

    model_classes = []
    for _, obj in getmembers(pyinaturalist.models):
        if isclass(obj) and issubclass(obj, BaseModel):
            model_classes.append(obj)
    return model_classes


# TODO: Also include @properties?
def get_model_doc(cls) -> List[Tuple[str, str, str]]:
    """Get the name, type and description for all model attributes. If an attribute has a validator
    with options, include those options in the description.
    """
    return [_get_field_doc(field) for field in cls.__attrs_attrs__]


def _get_field_doc(field: Attribute) -> Tuple[str, str, str]:
    from sphinx_autodoc_typehints import format_annotation

    field_type = format_annotation(field.type)
    doc = field.metadata.get('doc', '')
    if getattr(field.validator, 'options', None):
        options = ', '.join([opt for opt in field.validator.options if opt is not None])
        doc += f'\n\n**Options:** ``{options}``'
    return (f'**{field.name}**', field_type, doc)


def export_model_doc(model_name, doc_table):
    """Export attribute documentation for a model to a CSV file"""
    with open(join(MODEL_DOC_DIR, f'{model_name}.csv'), 'w') as f:
        csv.writer(f).writerows(doc_table)
