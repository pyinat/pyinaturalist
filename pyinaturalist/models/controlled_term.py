from typing import List

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, LazyProperty, User, define_model, field


@define_model
class Annotation(BaseModel):
    """:fa:`tag` An annotation, meaning a **controlled term value** applied by a **user** to an **observation**.
    Based on the schema of annotations from
    `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    concatenated_attr_val: str = field(default=None)
    controlled_attribute_id: int = field(default=None)
    controlled_value_id: int = field(default=None)
    user_id: int = field(default=None)
    uuid: str = field(default=None)
    vote_score: int = field(default=None)
    votes: List = field(factory=list)
    user: property = LazyProperty(User.from_json, type=User, doc='User who added the annotation')

    @property
    def values(self) -> List[str]:
        """Split pipe-delimited annotation values into separate tokens"""
        if not self.concatenated_attr_val:
            return []
        return self.concatenated_attr_val.split('|')

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.controlled_attribute_id,
            'Values': ', '.join(self.values),
            'Votes': self.vote_score,
            'User': self.user.login,
        }

    def __str__(self) -> str:
        return (
            f'[{self.controlled_attribute_id}] {self.concatenated_attr_val} '
            f'({len(self.votes)} votes)'
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

    def __str__(self):
        return f'[{self.id}] {self.label}'


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

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'Label': self.label,
            'Values': self.value_labels,
        }

    def __str__(self):
        return f'[{self.id}] {self.label}: {self.value_labels}'
