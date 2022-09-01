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


@define(auto_attribs=False, init=False, field_transformer=add_lazy_attrs)
class Annotation(BaseModel):
    """:fa:`tag` An annotation, meaning a **controlled term value** applied by a **user** to an **observation**.
    Based on the schema of annotations from
    `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    controlled_attribute_id: int = field(default=None)
    controlled_value_id: int = field(default=None)
    user_id: int = field(default=None)
    uuid: str = field(default=None)
    vote_score: int = field(default=None)
    votes: List = field(factory=list)
    user: property = LazyProperty(User.from_json, type=User, doc='User who added the annotation')

    # Manually loaded attributes
    term: Optional['ControlledTerm'] = field(default=None)
    value: Optional['ControlledTermValue'] = field(default=None)

    # Attributes that will only be used during init and then omitted
    temp_attrs = ['term_label', 'value_label']

    def __init__(self, **kwargs):
        # Allow passing term_label and value_label as shorthand for creating ControlledTerm + Value
        term_label = kwargs.pop('term_label', None)
        value_label = kwargs.pop('value_label', None)
        self.__attrs_init__(**kwargs)
        if term_label:
            self.term_label = term_label
        if value_label:
            self.value_label = value_label

    @property
    def term_label(self) -> str:
        """Convenience property for getting/setting the term label"""
        return self.term.label if self.term else str(self.controlled_attribute_id)

    @term_label.setter
    def term_label(self, label: str):
        if not self.term:
            self.term = ControlledTerm(id=self.controlled_attribute_id)
        self.term.label = label

    @property
    def value_label(self) -> str:
        """Convenience property for getting/setting the value label"""
        return self.value.label if self.value else str(self.controlled_value_id)

    @value_label.setter
    def value_label(self, label: str):
        if not self.value:
            self.value = ControlledTermValue(id=self.controlled_value_id)
        self.value.label = label

    # Unused attributes
    # concatenated_attr_val: str = field(default=None)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.controlled_attribute_id,
            'Value': self.controlled_value_id,
            'Votes': self.vote_score,
            'User': self.user.login,
        }

    def __str__(self) -> str:
        """Show term/value label if available, otherwise just IDs"""
        return f'{self.__class__.__name__}(term={self.term_label}, value={self.value_label})'


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


@define_model
class ControlledTermCount(BaseModel):
    """:fa:`tag` A count + histogram of a controlled term and value"""

    count: int = field(default=0, doc='')
    histogram: Dict[int, int] = field(factory=dict)
    term = LazyProperty(ControlledTerm.from_json, type=ControlledTerm)
    value = LazyProperty(ControlledTermValue.from_json, type=ControlledTermValue)

    @classmethod
    def from_json(cls, value: JsonResponse, user_id: int = None, **kwargs) -> 'ControlledTermCount':
        """Rename some response fields before initializing"""
        value['histogram'] = value.pop('month_of_year', None)
        value['term'] = value.pop('controlled_attribute', None)
        value['value'] = value.pop('controlled_value', None)
        return super(ControlledTermCount, cls).from_json(value)

    @property
    def term_label(self) -> str:
        return self.term.label

    @property
    def value_label(self) -> str:
        return self.value.label

    @property
    def _row(self) -> TableRow:
        return {
            'Term': self.term.label,
            'Value': self.value.label,
            'Count': self.count,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['term_label', 'value_label', 'count']


@define_model_collection
class ControlledTermCounts(BaseModelCollection):
    """:fa:`tag` :fa:`list` Used with
    :v1:`GET /observations/popular_field_values <Observations/get_observations_popular_field_values>`.
    """

    data: List[ControlledTermCount] = field(
        factory=list, converter=ControlledTermCount.from_json_list
    )
