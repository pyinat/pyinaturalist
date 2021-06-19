from typing import List

from attr import field

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, LazyProperty, User, define_model, kwarg


@define_model
class Annotation(BaseModel):
    """A dataclass containing information about an annotation, matching the schema of annotations
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    concatenated_attr_val: str = kwarg
    controlled_attribute_id: int = kwarg
    controlled_value_id: int = kwarg
    user_id: int = kwarg
    uuid: str = kwarg
    vote_score: int = kwarg
    votes: List = field(factory=list)
    user: property = LazyProperty(User.from_json)

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
            'Value': ', '.join(self.values),
            'Votes': self.vote_score,
            'User': self.user.login,
        }

    def __str__(self) -> str:
        return (
            f'[{self.controlled_attribute_id}] {self.concatenated_attr_val} '
            f'({len(self.votes)} votes)'
        )
