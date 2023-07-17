# ruff: noqa: E501
from copy import deepcopy
from typing import Dict, List, Optional

from attr import define

from pyinaturalist.constants import JsonResponse, TableRow
from pyinaturalist.models import (
    BaseModel,
    BaseModelCollection,
    LazyProperty,
    User,
    add_lazy_attrs,
    define_model,
    define_model_collection,
    field,
)


@define_model
class ControlledTermValue(BaseModel):
    """:fa:`tag` A controlled term **value**, based on the schema of
    `GET /controlled_terms <https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms>`_.
    """

    blocking: bool = field(default=None)
    label: str = field(default=None)
    ontology_uri: str = field(default=None)
    uri: str = field(default=None)
    uuid: str = field(default=None)
    taxon_ids: List[int] = field(factory=list)

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'label']


@define_model
class ControlledTerm(BaseModel):
    """:fa:`tag` A controlled term, based on the schema of
    `GET /controlled_terms <https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms>`_.
    """

    is_value: bool = field(default=None)
    multivalued: bool = field(default=None)
    label: str = field(default=None)
    ontology_uri: str = field(default=None)
    uri: str = field(default=None)
    uuid: str = field(default=None)
    taxon_ids: List[int] = field(factory=list)
    excepted_taxon_ids: List[int] = field(factory=list)
    values: property = LazyProperty(
        ControlledTermValue.from_json_list,
        type=List[ControlledTermValue],
        doc='Allowed values for this controlled term',
    )

    @property
    def value_labels(self) -> str:
        """Combined labels from all controlled term values"""
        return ', '.join([value.label for value in self.values])

    def get_value_by_id(self, controlled_value_id: int) -> Optional[ControlledTermValue]:
        """Get the value with the specified controlled value ID"""
        return next((v for v in self.values if v.id == controlled_value_id), None)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Label': self.label,
            'Values': self.value_labels,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'label', 'value_labels']


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Annotation(BaseModel):
    """:fa:`tag` An annotation, meaning a **controlled term value** applied by a **user** to an **observation**.
    Based on the schema of annotations from
    :v1:`GET /observations <Observations/get_observations>` and
    :v1:`GET /observations/{id} <Observations/get_observations_id>`.

    For convenience, an Annotation object may be initialized from labels::

        >>> Annotation(term='Life Stage', value='Adult')

    Or from IDs::

        >>> Annotation(controlled_attribute_id=1, controlled_value_id=2)

    Or from objects::

        >>> Annotation(
        ...     controlled_attribute=ControlledTerm(id=1, label='Life Stage'),
        ...     controlled_value_id=ControlledTermValue(id=2, label='Adult'),

    **Note:** Different annotation information is returned from different API endpoints:

    * ``GET /observations`` (used by :py:func:`~pyinaturalist.v1.observations.get_observations` and :py:meth:`.ObservationController.search`)
      returns annotations with term and value IDs only.
    * ``GET /observations/{id}`` (used by :py:func:`.get_observations_by_id()` and :py:meth:`.ObservationController.from_ids`)
      returns full annotations details, including labels.
    """

    user_id: int = field(default=None)
    uuid: str = field(default=None)
    vote_score: int = field(default=None)
    votes: List = field(factory=list)
    user: property = LazyProperty(User.from_json, type=User, doc='User who added the annotation')

    controlled_attribute: property = LazyProperty(
        ControlledTerm.from_json, type=User, doc='Term definition details'
    )
    controlled_value: property = LazyProperty(
        ControlledTermValue.from_json, type=User, doc='Annotation value details'
    )

    # Unused attributes
    # controlled_attribute_id: int = field(default=None)
    # controlled_value_id: int = field(default=None)
    # concatenated_attr_val: str = field(default=None)

    # Attributes that will only be used during init and then omitted
    temp_attrs = ['controlled_attribute_id', 'controlled_value_id', 'term', 'value']

    def __init__(self, **kwargs):
        # Allow passing term/value IDs only (as in observation API results)
        controlled_attribute_id = kwargs.pop('controlled_attribute_id', None)
        controlled_value_id = kwargs.pop('controlled_value_id', None)

        # Allow passing term/value labels only
        term = kwargs.pop('term', None)
        value = kwargs.pop('value', None)

        self.__attrs_init__(**kwargs)

        # Populate term/value objects from IDs and/or labels, if needed
        self.controlled_attribute = self.controlled_attribute or ControlledTerm()
        self.controlled_attribute.id = controlled_attribute_id or self.controlled_attribute.id
        self.controlled_attribute.label = self.controlled_attribute.label or term
        self.controlled_value = self.controlled_value or ControlledTermValue()
        self.controlled_value.id = controlled_value_id or self.controlled_value.id
        self.controlled_value.label = self.controlled_value.label or value

    @property
    def term(self) -> str:
        """Convenience property for getting/setting the controlled term label"""
        return self.controlled_attribute.label or str(self.controlled_attribute.id)

    @term.setter
    def term(self, label: str):
        self.controlled_attribute.label = label

    @property
    def value(self) -> str:
        """Convenience property for getting/setting the controlled value label"""
        return self.controlled_value.label or str(self.controlled_value.id)

    @value.setter
    def value(self, label: str):
        self.controlled_value.label = label

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.controlled_attribute.id,
            'Value': self.controlled_value.id,
            'Votes': self.vote_score,
            'User': self.user.login,
        }

    def __rich_repr__(self):
        yield 'term', self.term
        yield 'value', self.value

    def __str__(self) -> str:
        """Show term/value label if available, otherwise just IDs"""
        return f'{self.__class__.__name__}(term={self.term}, value={self.value})'


@define_model
class ControlledTermCount(BaseModel):
    """:fa:`tag` A count + histogram of a controlled term and value"""

    count: int = field(default=0, doc='')
    histogram: Dict[int, int] = field(factory=dict)
    controlled_attribute = LazyProperty(ControlledTerm.from_json, type=ControlledTerm)
    controlled_value = LazyProperty(ControlledTermValue.from_json, type=ControlledTermValue)

    @classmethod
    def from_json(
        cls, value: JsonResponse, user_id: Optional[int] = None, **kwargs
    ) -> 'ControlledTermCount':
        """Rename some response fields before initializing"""
        value = deepcopy(value)
        value['histogram'] = value.pop('month_of_year', None)
        return super(ControlledTermCount, cls).from_json(value)

    @property
    def term(self) -> str:
        return self.controlled_attribute.label

    @property
    def value(self) -> str:
        return self.controlled_value.label

    @property
    def _row(self) -> TableRow:
        return {
            'Term': self.term,
            'Value': self.value,
            'Count': self.count,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['term', 'value', 'count']


@define_model_collection
class ControlledTermCounts(BaseModelCollection):
    """:fa:`tag` :fa:`list` Used with
    :v1:`GET /observations/popular_field_values <Observations/get_observations_popular_field_values>`.
    """

    data: List[ControlledTermCount] = field(
        factory=list, converter=ControlledTermCount.from_json_list
    )
