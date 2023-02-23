"""Models for additional endpoint-specific metadata associated with a taxon"""
from typing import List, Optional

from pyinaturalist.constants import ESTABLISTMENT_MEANS, DateTime, TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Place,
    User,
    datetime_field,
    define_model_custom_init,
    define_model,
    field,
)


@define_model
class EstablishmentMeans(BaseModel):
    """:fa:`exclamation-triangle` The establishment means for a taxon in a given location"""

    establishment_means: str = field(
        default=None,
        options=ESTABLISTMENT_MEANS,
        converter=lambda x: str(x).lower(),
        doc='Establishment means label',
    )
    establishment_means_description: str = field(
        default=None, options=ESTABLISTMENT_MEANS, doc='Establishment means description'
    )
    place: property = LazyProperty(
        Place.from_json, type=Place, doc='Location that the establishment means applies to'
    )

    # TODO: Is establishment_means_label ever different from establishment_means?
    @property
    def establishment_means_label(self) -> str:
        return self.establishment_means

    @establishment_means_label.setter
    def establishment_means_label(self, value: str):
        self.establishment_means = value

    def __str__(self) -> str:
        return f'EstablishmentMeans({self.establishment_means})'


@define_model
class Checklist(BaseModel):
    """:fa:`dove` :fa:`list` A taxon checklist (aka
    `"original life list" <https://www.inaturalist.org/blog/43337-upcoming-changes-to-lists>`_)
    """

    title: str = field(default=None)


@define_model_custom_init
class ListedTaxon(EstablishmentMeans):
    """:fa:`dove` :fa:`list` A taxon with additional stats associated with a list
    (aka `"original life list" <https://www.inaturalist.org/blog/43337-upcoming-changes-to-lists>`_),
    based on the schema of:

    * ``Taxon.listed_taxa`` from :v1:`GET /taxa/{id} <Taxa/get_taxa_id>`
    * ``TaxonSummary.listed_taxon`` from  :v1:`GET /observations/{id}/taxon_summary <Observations/get_observations_id_taxon_summary>`
    """

    comments_count: int = field(default=0, doc='Number of comments for this listed taxon')
    created_at: DateTime = datetime_field(doc='Date and time the record was created')
    description: str = field(default=None, doc='Listed taxon description')
    first_observation_id: int = field(default=None, doc='Oldest recent observation ID in the list')
    last_observation_id: int = field(default=None, doc='Most recent observation ID in the list')
    list_id: int = field(default=None, repr=False)
    manually_added: bool = field(
        default=None, doc='Indicates if the taxon was manually added to the list'
    )
    observations_count: int = field(
        default=0, doc='Number of observations of this taxon in the list'
    )
    occurrence_status_level: int = field(default=None, doc='')
    primary_listing: bool = field(
        default=None, doc='Indicates if this is the primary listing for this taxon'
    )
    source_id: int = field(default=None, doc='')
    taxon_id: int = field(default=None, doc='')
    taxon_range_id: int = field(default=None, doc='')
    updated_at: DateTime = datetime_field(doc='Date and time the record was last updated')

    list: Checklist = field(default=None, converter=Checklist.from_json, doc='Associated checklist')
    updater: User = field(
        default=None, converter=User.from_json, doc='User that last updated the record'
    )
    user: User = field(default=None, converter=User.from_json, doc='User that created the record')

    # Attributes that will only be used during init and then omitted
    temp_attrs = ['list_id']

    def __init__(self, list_id: str = None, **kwargs):
        self.__attrs_init__(**kwargs)
        if list_id:
            self.list_id = list_id

    # Wrapper properties to handle some more inconsistencies between similar endpoints
    @property
    def list_id(self) -> Optional[int]:
        return self.list.id if self.list else None

    @list_id.setter
    def list_id(self, value: int):
        if not self.list:
            self.list = Checklist()
        self.list.id = value

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
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Taxon ID': self.taxon_id,
            'Place ID': self.place.id,
            'Life list': self.list.title or self.list.id,
            'Establishment means': self.establishment_means,
            'Observations': self.observations_count,
            'Comments': self.comments_count,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'taxon_id', 'place', 'establishment_means', 'observations_count']

    def __str__(self) -> str:
        return BaseModel.__str__(self)
