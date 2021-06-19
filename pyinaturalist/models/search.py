from typing import List, Union

from attr import field

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, Place, Project, Taxon, User, define_model, kwarg

SEARCH_RESULT_TYPES = {cls.__name__: cls for cls in [Place, Project, Taxon, User]}
SEARCH_RESULT_TITLES = {'Place': 'name', 'Project': 'title', 'Taxon': 'full_name', 'User': 'login'}
SearchResultRecord = Union[Place, Project, Taxon, User]


@define_model
class SearchResult(BaseModel):
    """A dataclass for search results, matching the schema of
    `GET /search <https://api.inaturalist.org/v1/docs/#!/Search/get_search>`_.
    """

    score: float = field(default=0)
    type: str = kwarg  # Enum
    matches: List[str] = field(factory=list)
    record: SearchResultRecord = kwarg

    # Convert value by datatype
    def __attrs_post_init__(self):
        if self.type in SEARCH_RESULT_TYPES and self.record is not None:
            result_cls = SEARCH_RESULT_TYPES[self.type]
            self.record = result_cls.from_json(self.record)

    @property
    def record_name(self) -> str:
        name_attr = SEARCH_RESULT_TITLES[self.type]
        return getattr(self.record, name_attr)

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.record.id,
            'Type': self.type,
            'Score': f'{self.score:.2f}',
            'Name': self.record_name,
        }

    def __str__(self) -> str:
        return f'[{self.type}] {self.record}'
