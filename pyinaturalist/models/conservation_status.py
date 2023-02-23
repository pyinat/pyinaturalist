"""Models for additional taxon conservation statuses"""
import re
from typing import List, Optional

from attr import define

from pyinaturalist.constants import DateTime
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Place,
    ListedTaxon,
    User,
    datetime_field,
    define_model,
    field,
    upper,
)


@define
class IUCNStatus:
    id: int = field()
    code: str = field()
    description: str = field()


# IUCN Conservation status IDs and codes from https://www.iucnredlist.org
IUCN_STATUSES = [
    IUCNStatus(0, 'NE', 'not evaluated'),
    IUCNStatus(5, 'DD', 'data deficient'),
    IUCNStatus(10, 'LC', 'least concern'),
    IUCNStatus(20, 'NT', 'near threatened'),
    IUCNStatus(30, 'VU', 'vulnerable'),
    IUCNStatus(40, 'EN', 'endangered'),
    IUCNStatus(50, 'CR', 'critically endangered'),
    IUCNStatus(60, 'EW', 'extinct in the wild'),
    IUCNStatus(70, 'EX', 'extinct'),
]
IUCN_STATUSES_BY_CODE = {s.code: s.description for s in IUCN_STATUSES}
IUCN_STATUSES_BY_ID = {s.id: s.description for s in IUCN_STATUSES}

# Levels may be in ranges, and prefixed with a regional level, e.g. S2S3
# https://www.natureserve.org/nsexplorer/about-the-data/statuses/conservation-status-categories
NATURESERVE_STATUS_CODES = {
    'X': 'extinct',
    'H': 'possibly extinct',
    '1': 'critically imperiled',
    '2': 'imperiled',
    '3': 'vulnerable',
    '4': 'apparently secure',
    '5': 'secure',
}

# https://www.dof.gob.mx/normasOficiales/4254/semarnat/semarnat.htm
NORMA_OFICIAL_059_STATUS_CODES = {
    'P': 'en peligro de extinción',
    'A': 'amenazada',
    'PR': 'sujeta a protección especial',
    'EX': 'probablemente extinta en el medio silvestre',
}

# Generic status codes not associated with a specific authority
GENERIC_STATUS_CODES = {
    'SE': 'endangered',
    'FE': 'endangered',
    'LE': 'endangered',
    'E': 'endangered',
    'ST': 'threatened',
    'FT': 'threatened',
    'LT': 'threatened',
    'T': 'threatened',
    'LC': 'least concern',
    'SC': 'special concern',
    'C': 'candidate',
}


@define_model
class ConservationStatus(BaseModel):
    """:fa:`exclamation-triangle` The conservation status of a taxon in a given location, based on the schema of:

    * ``Taxon.conservation_status`` from :v1:`GET /taxa <Taxa/get_taxa>`
    * ``Observation.taxon.conservation_statuses`` from :v1:`GET /observations <Observations/get_observations>`
    * ``conservation_status`` from :v1:`GET /observation/{id}/taxon_summary <Observations/get_observations_id_taxon_summary>`
    """

    authority: str = field(default=None, doc='Data source for conservation status')
    created_at: DateTime = datetime_field(doc='Date and time the record was created')
    description: str = field(default=None, doc='Description of conservation status')
    geoprivacy: str = field(
        default=None,
        doc='Default geoprivacy level; may be obscured or private for protected species',
    )
    iucn: int = field(default=None, doc='IUCN ID, if applicable')
    source_id: int = field(default=None)
    status: str = field(default=None, converter=upper, doc='Short code for conservation status')
    status_name: str = field(default=None, doc='Full name of conservation status')
    taxon_id: int = field(default=None, doc='Taxon ID')
    updated_at: DateTime = datetime_field(doc='Date and time the record was last updated')
    url: str = field(default=None, doc='Link to data source with more details')

    # Lazy-loaded nested model objects
    place: property = LazyProperty(  # type: ignore
        Place.from_json, type=Place, doc='Location that the conservation status applies to'
    )
    updater: User = LazyProperty(User.from_json, type=User, doc='User that last updated the record')  # type: ignore
    user: User = LazyProperty(User.from_json, type=User, doc='User that created the record')  # type: ignore

    # TODO: Are these needed? They appear to be redundant with `status` and `status_name`
    # iucn_status: str = field(default=None)
    # iucn_status_code: str = field(default=None)

    @property
    def full_name(self) -> str:
        """Get a full returns the name, code, and place in a format like
        _'imperiled (S2S3B) in Nova Scotia, CA'_
        """
        return f'{self.status_name} ({self.status}) in {self.place.name}'

    # Wrapper properties to handle inconsistencies between obs, taxa, and taxon_summary endpoints
    @property
    def place_id(self) -> Optional[int]:
        return self.place.id if self.place else None

    @place_id.setter
    def place_id(self, value: int):
        self.place = Place(id=value)

    @property
    def updater_id(self) -> Optional[int]:
        return self.updater.id if self.updater else None

    @updater_id.setter
    def updater_id(self, value: int):
        self.updater = User(id=value)

    @property
    def user_id(self) -> Optional[int]:
        return self.user.id if self.user else None

    @user_id.setter
    def user_id(self, value: int):
        self.user = User(id=value)

    @property
    def _str_attrs(self) -> List[str]:
        return ['status_name', 'status', 'place', 'authority']


@define_model
class TaxonSummary(BaseModel):
    """:fa:`dove` :fa:`list` Information about an observation's taxon, within the context
    of the observation's location. Based on the schema of
    :v1:`GET /observations/{id}/taxon_summary <Observations/get_observations_id_taxon_summary>`
    """

    conservation_status: property = LazyProperty(
        ConservationStatus.from_json,
        type=ConservationStatus,
        doc='Conservation status of the taxon in the observation location',
    )
    listed_taxon: property = LazyProperty(
        ListedTaxon.from_json,
        type=ListedTaxon,
        doc='Details about the taxon on an "original" life list',
    )
    wikipedia_summary: str = field(default=None, doc='Taxon summary from Wikipedia article')

    @property
    def _str_attrs(self) -> List[str]:
        return ['conservation_status', 'listed_taxon']


def translate_status_code(status: str, iucn_id: int = -1, authority: str = '') -> str:
    """Translate a conservation status code from a given authority into a descriptive name"""
    status = status.upper()
    authority = authority.lower()

    if authority == 'iucn':
        return IUCN_STATUSES_BY_CODE[status]
    elif authority == 'natureserve':
        return translate_natureserve_code(status)
    elif authority == 'norma_oficial_059':
        return NORMA_OFICIAL_059_STATUS_CODES[status]
    elif status in GENERIC_STATUS_CODES:
        return GENERIC_STATUS_CODES[status]
    elif iucn_id in IUCN_STATUSES_BY_ID:
        return IUCN_STATUSES_BY_ID[iucn_id]
    else:
        raise ValueError(
            f'Could not parse conservation status code: {status} From authority: {authority}'
        )


def translate_natureserve_code(status: str) -> str:
    """Translate a NatureServe status code to a status name, including level ranges"""
    if status in NATURESERVE_STATUS_CODES:
        return NATURESERVE_STATUS_CODES[status]

    match = re.match(r'\D+([\dXH])(?:\D+([\dXH]))?', status)
    if not match:
        raise ValueError(f'Could not parse NatureServe status code: {status}')

    levels = [int(lvl) for lvl in match.groups() if lvl]
    # Single level
    if len(levels) == 1:
        level = levels[0]
    # Level range spanning 3 levels; pick average
    elif levels[1] - levels[0] == 2:
        level = levels[0] + 1
    # Level range spanning 2 levels; pick higher
    elif levels[1] - levels[0] == 1:
        level = levels[0]
    else:
        print(levels)
        print(levels[1] - levels[0])
        raise ValueError(f'Could not parse NatureServe level range: {status}')

    return NATURESERVE_STATUS_CODES[str(level)]


assert translate_natureserve_code('S2') == 'imperiled'
assert translate_natureserve_code('G2') == 'imperiled'
assert translate_natureserve_code('S2S3B') == 'imperiled'
assert translate_natureserve_code('N2N4') == 'vulnerable'
