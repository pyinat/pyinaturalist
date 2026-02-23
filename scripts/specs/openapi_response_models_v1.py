# Auto-generated classes from OpenAPI spec
from datetime import date, datetime
from typing import Any, Literal


class Annotation:
    uuid: str
    controlled_attribute_id: int
    controlled_value_id: int
    concatenated_attr_val: str
    user: 'User'
    user_id: int
    vote_score: int
    votes: list['Vote']


class AutocompleteTaxon:
    pass


class BaseResponse:
    total_results: int
    page: int
    per_page: int


class Color:
    id: int
    value: str


class Comment:
    id: int
    body: str
    created_at: datetime
    created_at_details: 'DateDetails'
    user: 'User'
    flags: list['Flag']
    hidden: bool
    moderator_actions: list['ModeratorAction']
    uuid: str


class ConservationStatus:
    place_id: int
    place: 'CorePlace'
    status: str


class CorePlace:
    id: int
    name: str
    display_name: str


class CoreTaxon:
    id: int
    iconic_taxon_id: int
    iconic_taxon_name: str
    is_active: bool
    name: str
    preferred_common_name: str
    rank: str
    rank_level: float


class DateDetails:
    date: date
    day: int
    hour: int
    month: int
    week: int
    year: int


class EstablishmentMeans:
    establishment_means: str
    place: 'CorePlace'


class Fave:
    id: int
    votable_id: int
    created_at: datetime
    user: 'User'


class FieldValue:
    name: str
    value: str


class Identification:
    id: int
    observation_id: int
    body: str
    category: Literal['improving', 'leading', 'maverick', 'supporting']
    created_at: datetime
    updated_at: datetime
    current: bool
    taxon: 'ObservationTaxon'
    previous_observation_taxon: 'ObservationTaxon'
    user: 'User'
    uuid: str
    created_at_details: 'DateDetails'
    flags: list['Flag']
    own_observation: bool
    taxon_change: dict
    vision: bool
    disagreement: bool
    previous_observation_taxon_id: int
    spam: bool
    hidden: bool
    moderator_actions: list['ModeratorAction']


class Message:
    id: int
    subject: str
    body: str
    user_id: int
    to_user: 'User'
    from_user: 'User'
    thread_id: int
    thread_messages_count: int
    thread_flags: list[dict]


class ModeratorAction:
    id: int
    created_at: datetime
    created_at_details: 'DateDetails'
    user: 'User'
    action: Literal['hide', 'rename', 'unhide', 'suspend', 'unsuspend']
    reason: str


class NonOwnerIdentification:
    id: int
    body: str
    created_at: datetime
    created_at_details: 'DateDetails'
    user: 'User'


class Observation:
    annotations: list['Annotation']
    id: int
    cached_votes_total: int
    captive: bool
    comments: list['Comment']
    comments_count: int
    created_at: datetime
    created_at_details: 'DateDetails'
    created_time_zone: str
    description: str
    faves_count: int
    geojson: 'PointGeoJson'
    geoprivacy: str
    taxon_geoprivacy: str
    id_please: bool
    identifications_count: int
    identifications_most_agree: bool
    identifications_most_disagree: bool
    identifications_some_agree: bool
    license_code: str
    location: str
    private_location: str
    mappable: bool
    non_owner_ids: list['NonOwnerIdentification']
    num_identification_agreements: int
    num_identification_disagreements: int
    obscured: bool
    observed_on: datetime
    observed_on_details: 'DateDetails'
    observed_on_string: str
    observed_time_zone: str
    ofvs: list['FieldValue']
    out_of_range: bool
    photos: list['Photo']
    place_guess: str
    private_place_guess: str
    place_ids: list[int]
    private_place_ids: list[int]
    positional_accuracy: int
    private_geojson: 'PointGeoJson'
    project_ids: list[int]
    project_ids_with_curator_id: list[int]
    project_ids_without_curator_id: list[int]
    public_positional_accuracy: int
    quality_grade: str
    reviewed_by: list[int]
    site_id: int
    sounds: list['Sound']
    species_guess: str
    tags: list[str]
    taxon: 'ObservationTaxon'
    time_observed_at: datetime
    time_zone_offset: str
    updated_at: datetime
    uri: str
    user: 'User'
    uuid: str
    verifiable: bool
    observation_photos: list['ObservationPhoto']
    quality_metrics: list['QualityMetric']
    flags: list['Flag']
    community_taxon_id: int
    faves: list['Fave']
    identifications: list['Identification']
    oauth_application_id: int
    outlinks: list['Outlink']
    owners_identification_from_vision: bool
    preferences: dict
    project_observations: list['ProjectObservation']
    spam: bool
    votes: list['Vote']
    identification_disagreements_count: int
    ident_taxon_ids: list[int]
    map_scale: int


class ObservationPhoto:
    id: int
    uuid: str
    photo: 'Photo'
    position: int


class QualityMetric:
    id: int
    user_id: int
    metric: str
    agree: bool


class Flag:
    id: int
    flag: str
    comment: str
    resolved: bool
    user: 'User'
    created_at: datetime


class Outlink:
    id: int
    source: str
    url: str


class ProjectObservation:
    id: int
    project_id: int
    observation_id: int
    curator_identification_id: int
    tracking_code: str
    prefers_curator_coordinate_access: bool


class Vote:
    id: int
    user_id: int
    vote_flag: bool
    vote_scope: str
    created_at: datetime


class ObservationTaxon:
    pass


class Photo:
    id: int
    attribution: str
    license_code: str
    url: str


class PointGeoJson:
    type: str
    coordinates: list[float]


class PolygonGeoJson:
    type: str
    coordinates: list[list[list[float]]]


class Project:
    id: int
    title: str
    description: str
    slug: str


class ProjectMember:
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    role: Literal['curator', 'manager']
    observations_count: int
    taxa_count: int
    user: 'User'


class RawConservationStatus:
    source_id: int
    authority: str
    status: str
    status_name: str
    iucn: int
    geoprivacy: str


class TaxonConservationStatus:
    pass


class ShowObservation:
    pass


class ShowPlace:
    pass


class ShowTaxon:
    pass


class Sound:
    id: int
    attribution: str
    license_code: str


class TaxonPhoto:
    pass


class User:
    created_at: datetime
    id: int
    icon: str
    icon_url: str
    identifications_count: int
    journal_posts_count: int
    login: str
    name: str
    observations_count: int
    orcid: str
    roles: list[Literal['admin', 'app owner', 'curator']]
    site_id: int
    species_count: int
    spam: bool
    suspended: bool


class MessagesResponse:
    pass


class NearbyPlacesResponse:
    pass


class ObservationsResponse:
    pass


class ObservationsShowResponse:
    pass


class UserCountsResponse:
    pass


class ObservationsObserversResponse:
    pass


class SpeciesCountsResponse:
    pass


class PlacesResponse:
    pass


class ProjectMembersResponse:
    pass


class ProjectsResponse:
    pass


class TaxaAutocompleteResponse:
    pass


class TaxaShowResponse:
    pass


class UTFGridResponse:
    grid: list[str]
    keys: list[str]
    data: dict


class Error:
    code: int
    message: str
