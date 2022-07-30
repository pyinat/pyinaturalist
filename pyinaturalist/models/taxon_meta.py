"""Models for additional endpoint-specific metadata associated with a taxon"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from pyinaturalist.constants import CONSERVATION_STATUSES, ESTABLISTMENT_MEANS, DateTime, TableRow
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Place,
    User,
    datetime_field,
    define_model,
    field,
    upper,
)


class IdWrapperMixin(ABC):
    """Mixin to handle some inconsitencies between similar endpoints. If just an ID is received for
    place, user, or updater, this turns them into partial records. So, for example, the user ID can
    always be accessed via ``<object>.user.id``.
    """

    __slots__ = ()

    @abstractmethod
    def __init__(self):
        if TYPE_CHECKING:
            self.place = LazyProperty()
            self.updater = LazyProperty()
            self.user = LazyProperty()

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


# TODO: Include codes from other sources? Currently only including IUCN codes.
@define_model
class ConservationStatus(IdWrapperMixin, BaseModel):
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
    iucn: int = field(default=None, doc='IUCD ID, if applicable')
    source_id: int = field(default=None)
    status: str = field(
        default=None,
        converter=upper,
        options=CONSERVATION_STATUSES,
        doc='Short code for conservation status',
    )
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
    def _str_attrs(self) -> List[str]:
        return ['status_name', 'status', 'authority']


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


@define_model
class ListedTaxon(IdWrapperMixin, EstablishmentMeans):
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

    def __attrs_post_init__(self):
        """Handle differences between taxa and taxon_summary endpoints"""
        if not self.list.id:
            self.list.id = self.list_id

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
