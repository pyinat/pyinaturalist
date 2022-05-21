from typing import List, Union

from pyinaturalist.constants import TableRow
from pyinaturalist.models import BaseModel, Place, Project, Taxon, User, define_model, field

SEARCH_RESULT_TYPES = {cls.__name__: cls for cls in [Place, Project, Taxon, User]}
SEARCH_RESULT_TITLES = {'Place': 'name', 'Project': 'title', 'Taxon': 'full_name', 'User': 'login'}
SearchResultRecord = Union[Place, Project, Taxon, User]


@define_model
class SearchResult(BaseModel):
    """:fa:`search` A search result of any type, based on the schema of
    `GET /search <https://api.inaturalist.org/v1/docs/#!/Search/get_search>`_.
    """

    score: float = field(default=0, doc='Search result rank')
    type: str = field(default=None, options=SEARCH_RESULT_TYPES, doc='Search result type')
    matches: List[str] = field(factory=list, doc='Search terms matched')
    record: SearchResultRecord = field(default=None, doc='Search result object')

    # Convert value by datatype
    def __attrs_post_init__(self):
        if self.type in SEARCH_RESULT_TYPES and self.record is not None:
            result_cls = SEARCH_RESULT_TYPES[self.type]
            self.record = result_cls.from_json(self.record)

    @property
    def record_name(self) -> str:
        """Alias for type-specific name/title field"""
        name_attr = SEARCH_RESULT_TITLES[self.type]
        return getattr(self.record, name_attr)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.record.id,
            'Type': self.type,
            'Score': f'{self.score:.2f}',
            'Name': self.record_name,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'type', 'score', 'record_name']
