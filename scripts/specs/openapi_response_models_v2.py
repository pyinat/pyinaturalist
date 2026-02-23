# Auto-generated classes from OpenAPI spec
from datetime import date, datetime
from typing import Any, Literal


class ControlledTerm:
    id: int
    blocking: bool
    is_value: bool
    excepted_taxon_ids: list[int]
    label: str
    labels: list[dict]
    multivalued: bool
    ontology_uri: str
    taxon_ids: list[int]
    uri: str
    uuid: str
    valid_within_clade: int
    values: list['ControlledTerm']


class Site:
    id: int
    icon_url: str
    locale: str
    name: str
    place_id: int
    site_name_short: str
    url: str


class User:
    id: int
    uuid: str
    created_at: datetime
    description: str
    faved_project_ids: list[float]
    icon: str
    icon_url: str
    identifications_count: int
    journal_posts_count: int
    annotated_observations_count: int
    last_active: datetime
    login: str
    monthly_supporter: bool
    name: str
    observations_count: int
    orcid: str
    preferences: dict
    roles: list[str]
    site: 'Site'
    site_id: int
    spam: bool
    species_count: int
    suspended: bool
    updated_at: datetime


class Vote:
    id: int
    created_at: str
    user: 'User'
    user_id: int
    vote_flag: bool
    vote_scope: str


class Annotation:
    concatenated_attr_val: str
    controlled_attribute: 'ControlledTerm'
    controlled_attribute_id: int
    controlled_value: 'ControlledTerm'
    controlled_value_id: int
    user: 'User'
    user_id: int
    uuid: str
    vote_score: int
    votes: list['Vote']


class Announcement:
    id: int
    body: str
    placement: str
    clients: list[str]
    dismissible: bool
    locales: list[str]
    start: datetime
    end: datetime


class AppBuildInfo:
    rails: dict
    api: dict
    vision: dict


class AuthorizedApplication:
    application: dict
    created_at: datetime
    scopes: list[Literal['login', 'write', 'account_delete']]


class BuildInfo:
    git_branch: str
    git_commit: str
    image_tag: str
    build_date: str


class DateDetails:
    date: str
    day: int
    hour: int
    month: int
    week: int
    year: int


class Flag:
    id: int
    comment: str
    created_at: datetime
    created_at_utc: datetime
    flag: str
    flaggable_content: str
    flaggable_id: int
    flaggable_type: str
    flaggable_user_id: int
    resolved: bool
    resolver_id: int
    resolved_at: datetime
    updated_at: datetime
    updated_at_utc: datetime
    user: 'User'
    user_id: int
    uuid: str


class ModeratorAction:
    id: int
    created_at: str
    created_at_details: 'DateDetails'
    user: 'User'
    action: str
    reason: str
    private: bool


class Comment:
    id: int
    body: str
    created_at: datetime
    created_at_details: 'DateDetails'
    created_at_utc: datetime
    flags: list['Flag']
    hidden: bool
    html: str
    moderator_actions: list['ModeratorAction']
    parent_id: int
    parent_type: str
    user: 'User'
    user_id: int
    updated_at: datetime
    updated_at_details: datetime
    uuid: str


class Taxon:
    id: int
    uuid: str
    ancestors: list['Taxon']
    ancestor_ids: list[int]
    ancestry: str
    atlas_id: int
    children: list['Taxon']
    complete_rank: str
    complete_species_count: int
    conservation_status: 'ConservationStatus'
    conservation_statuses: list['ConservationStatus']
    created_at: str
    current_synonymous_taxon_ids: list[int]
    default_photo: 'Photo'
    endemic: bool
    english_common_name: str
    establishment_means: dict
    preferred_establishment_means: str
    extinct: bool
    provisional: bool
    flag_counts: dict
    iconic_taxon_id: int
    iconic_taxon_name: str
    introduced: bool
    is_active: bool
    listed_taxa: list[dict]
    listed_taxa_count: int
    matched_term: str
    min_species_ancestry: str
    min_species_taxon_id: int
    name: str
    native: bool
    observations_count: int
    parent_id: int
    photos_locked: bool
    preferred_common_name: str
    preferred_common_names: list[Any]
    rank: str
    rank_level: float
    representative_photo: 'Photo'
    statuses: list[Any]
    taxon_changes_count: int
    taxon_photos: list[dict]
    taxon_schemes_count: int
    threatened: bool
    universal_search_rank: int
    vision: bool
    wikipedia_summary: str
    wikipedia_url: str


class ConservationStatus:
    id: int
    authority: str
    description: str
    geoprivacy: str
    iucn: int
    iucn_status: str
    iucn_status_code: str
    place: dict
    place_id: int
    source_id: int
    status: str
    status_name: str
    taxon_id: int
    user_id: int
    url: str


class Photo:
    id: int
    attribution: str
    attribution_name: str
    flags: list['Flag']
    hidden: bool
    large_url: str
    license_code: str
    medium_url: str
    moderator_actions: list['ModeratorAction']
    native_page_url: str
    native_photo_id: str
    original_dimensions: dict
    original_url: str
    small_url: str
    square_url: str
    type: str
    url: str
    original_filename: str


class List:
    id: int
    title: str


class PolygonGeoJson:
    type: str
    coordinates: Any


class PointGeoJson:
    coordinates: list[float]
    type: str


class Place:
    id: int
    admin_level: int
    ancestor_place_ids: list[int]
    bbox_area: float
    bounding_box_geojson: 'PolygonGeoJson'
    display_name: str
    display_name_autocomplete: str
    geometry_geojson: 'PolygonGeoJson'
    location: str
    matched_term: str
    name: str
    observations_count: int
    place_type: int
    point_geojson: 'PointGeoJson'
    slug: str
    universal_search_rank: int
    user: 'User'
    uuid: str
    without_check_list: bool


class CommonAncestor:
    score: float
    taxon: 'Taxon'


class Error:
    status: str
    errors: list[dict]


class IdSummaryReference:
    id: int
    id_summary_id: int
    reference_uuid: str
    reference_source: str
    reference_observation_id: int
    reference_date: datetime
    reference_content: str
    user_id: int
    user_login: str
    created_at: datetime
    updated_at: datetime


class IdSummary:
    id: int
    taxon_id_summary_id: int
    summary: str
    photo_tip: str
    visual_key_group: str
    score: float
    created_at: datetime
    updated_at: datetime
    references: list['IdSummaryReference']


class Identification:
    id: int
    body: str
    category: str
    created_at: datetime
    created_at_details: 'DateDetails'
    current: bool
    disagreement: bool
    flags: list['Flag']
    hidden: bool
    moderator_actions: list['ModeratorAction']
    observation_id: int
    own_observation: bool
    previous_observation_taxon_id: int
    previous_observation_taxon: 'Taxon'
    spam: bool
    taxon: 'Taxon'
    taxon_change: dict
    taxon_change_id: int
    taxon_change_type: str
    taxon_id: int
    updated_at: datetime
    user: 'User'
    user_id: int
    uuid: str
    vision: bool


class ListedTaxon:
    description: str
    place: 'Place'
    id: int
    created_at: str
    updated_at: str
    comments_count: int
    occurrence_status_level: int
    establishment_means: Literal['native', 'endemic', 'introduced']
    observations_count: int
    manually_added: bool
    primary_listing: bool
    establishment_means_label: str
    establishment_means_description: str


class Message:
    id: int
    user_id: int
    thread_id: int
    subject: str
    body: str
    read_at: datetime
    created_at: datetime
    updated_at: datetime
    comments_count: int
    from_user: 'User'
    to_user: 'User'


class ObservationField:
    id: int
    allowed_values: str
    datatype: str
    description: str
    description_autocomplete: str
    name: str
    name_autocomplete: str
    users_count: int
    uuid: str
    values_count: int


class Project:
    id: int
    admins: list[dict]
    banner_color: str
    created_at: str
    delegated_project_id: int
    description: str
    flags: list['Flag']
    header_image_contain: bool
    header_image_file_name: str
    header_image_url: str
    hide_title: bool
    hide_umbrella_map_flags: bool
    icon: str
    icon_file_name: str
    is_delegated_umbrella: bool
    is_umbrella: bool
    latitude: str
    location: str
    longitude: str
    observation_requirements_updated_at: datetime
    place_id: int
    prefers_user_trust: bool
    project_observation_fields: list[dict]
    project_observation_rules: list[dict]
    project_type: str
    rule_preferences: list[dict]
    search_parameters: list[dict]
    site_features: list[dict]
    slug: str
    terms: str
    title: str
    updated_at: str
    user: 'User'
    user_id: int
    user_ids: list[int]


class ObservationPhoto:
    id: int
    photo: 'Photo'
    position: int
    uuid: str


class Sound:
    attribution: str
    file_content_type: str
    file_url: str
    flags: list['Flag']
    hidden: bool
    id: int
    license_code: str
    moderator_actions: list['ModeratorAction']
    native_sound_id: str
    original_filename: str


class ObservationSound:
    id: int
    sound: 'Sound'
    position: int
    uuid: str


class ObservationFieldValue:
    id: int
    datatype: str
    field_id: int
    name: str
    name_ci: str
    observation_field: 'ObservationField'
    taxon: 'Taxon'
    taxon_id: str
    user: 'User'
    user_id: int
    uuid: str
    value: str
    value_ci: str


class ProjectUser:
    id: int
    observations_count: int
    prefers_curator_coordinate_access_for: str
    project_id: int
    role: str
    taxa_count: int
    user_id: int
    created_at: datetime
    created_at_utc: datetime
    updated_at: datetime
    updated_at_utc: datetime


class ProjectObservation:
    id: int
    current_user_is_member: bool
    preferences: dict
    project: 'Project'
    project_id: int
    project_user: 'ProjectUser'
    user: 'User'
    user_id: int
    uuid: str


class QualityMetric:
    id: int
    agree: bool
    metric: str
    user: 'User'
    user_id: int


class Observation:
    id: int
    annotations: list['Annotation']
    application: dict
    cached_votes_total: int
    captive: bool
    comments: list['Comment']
    comments_count: int
    community_taxon: 'Taxon'
    community_taxon_id: int
    context_geoprivacy: str
    context_taxon_geoprivacy: str
    context_user_geoprivacy: str
    created_at: str
    created_at_details: 'DateDetails'
    created_time_zone: str
    description: str
    faves: list['Vote']
    faves_count: int
    flags: list['Flag']
    geojson: 'PointGeoJson'
    geoprivacy: str
    id_please: bool
    ident_taxon_ids: list[int]
    identifications: list['Identification']
    identifications_count: int
    identifications_most_agree: bool
    identifications_most_disagree: bool
    identifications_some_agree: bool
    license_code: str
    location: str
    map_scale: int
    mappable: bool
    non_owner_ids: list['Identification']
    non_traditional_projects: list[dict]
    num_identification_agreements: int
    num_identification_disagreements: int
    oauth_application_id: int
    obscured: bool
    observation_photos: list['ObservationPhoto']
    observation_sounds: list['ObservationSound']
    observed_on: str
    observed_on_details: 'DateDetails'
    observed_on_string: str
    observed_time_zone: str
    ofvs: list['ObservationFieldValue']
    out_of_range: bool
    outlinks: list[dict]
    owners_identification_from_vision: bool
    photos: list['Photo']
    place_guess: str
    place_ids: list[int]
    positional_accuracy: int
    preferences: dict
    private_geojson: 'PointGeoJson'
    private_location: str
    private_place_guess: str
    project_ids: list[int]
    project_ids_with_curator_id: list[int]
    project_ids_without_curator_id: list[int]
    project_observations: list['ProjectObservation']
    public_positional_accuracy: int
    quality_grade: str
    quality_metrics: list['QualityMetric']
    reviewed_by: list[int]
    site_id: int
    sounds: list['Sound']
    spam: bool
    species_guess: str
    tags: list[str]
    taxon: 'Taxon'
    taxon_geoprivacy: str
    time_observed_at: str
    time_zone_offset: str
    updated_at: str
    uri: str
    user: 'User'
    uuid: str
    viewer_trusted_by_observer: bool
    votes: list['Vote']


class TaxonNamePriority:
    id: int
    user_id: int
    place_id: int
    place: dict
    lexicon: str
    position: int


class PrivateUser:
    id: int
    uuid: str
    created_at: datetime
    description: str
    faved_project_ids: list[float]
    icon: str
    icon_url: str
    identifications_count: int
    journal_posts_count: int
    annotated_observations_count: int
    last_active: datetime
    monthly_supporter: bool
    name: str
    observations_count: int
    orcid: str
    roles: list[str]
    site: 'Site'
    site_id: int
    spam: bool
    species_count: int
    suspended: bool
    updated_at: datetime
    activity_count: int
    blocked_user_ids: list[int]
    confirmed_at: datetime
    confirmation_sent_at: datetime
    data_transfer_consent: bool
    email: str
    locale: str
    login: str
    muted_user_ids: list[int]
    pi_consent: bool
    place_id: int
    preferences: dict
    preferred_observation_fields_by: str
    preferred_observation_license: str
    preferred_photo_license: str
    preferred_project_addition_by: str
    preferred_sound_license: str
    prefers_automatic_taxonomic_changes: bool
    prefers_comment_email_notification: bool
    prefers_common_names: bool
    prefers_community_taxa: bool
    prefers_identification_email_notification: bool
    prefers_infraspecies_identification_notifications: bool
    prefers_mention_email_notification: bool
    prefers_message_email_notification: bool
    prefers_monthly_supporter_badge: bool
    prefers_no_email: bool
    prefers_no_tracking: bool
    prefers_non_disagreeing_identification_notifications: bool
    prefers_project_added_your_observation_email_notification: bool
    prefers_project_curator_change_email_notification: bool
    prefers_project_journal_post_email_notification: bool
    prefers_receive_mentions: bool
    prefers_redundant_identification_notifications: bool
    prefers_scientific_name_first: bool
    prefers_taxon_change_email_notification: bool
    prefers_taxon_or_place_observation_email_notification: bool
    prefers_user_observation_email_notification: bool
    privileges: list[str]
    search_place_id: int
    taxon_name_priorities: list['TaxonNamePriority']
    time_zone: str
    unconfirmed_email: str
    universal_search_rank: int


class ProjectMembership:
    id: int
    project_id: int
    role: str
    created_at: datetime
    updated_at: datetime
    prefers_curator_coordinate_access_for: str
    prefers_updates: bool


class ProviderAuthorization:
    created_at: datetime
    id: int
    provider_name: Literal['apple', 'facebook', 'flickr', 'google_oauth2', 'open_id', 'orcid', 'soundcloud', 'twitter']
    provider_uid: str
    scope: str
    updated_at: datetime
    user_id: int


class Relationship:
    id: int
    created_at: datetime
    updated_at: datetime
    user: 'User'
    friend_user: 'User'
    following: bool
    trust: bool
    reciprocal_trust: bool


class ResultsAnnotations:
    total_results: int
    page: int
    per_page: int
    results: list['Annotation']


class ResultsAnnouncements:
    total_results: int
    page: int
    per_page: int
    results: list['Announcement']


class ResultsAuthorizedApplications:
    total_results: int
    page: int
    per_page: int
    results: list['AuthorizedApplication']


class ResultsComments:
    total_results: int
    page: int
    per_page: int
    results: list['Comment']


class ResultsComputervision:
    total_results: int
    page: int
    per_page: int
    common_ancestor: 'CommonAncestor'
    experimental: str
    results: list[dict]


class ResultsControlledTerms:
    total_results: int
    page: int
    per_page: int
    results: list['ControlledTerm']


class ResultsEmailAvailable:
    available: bool


class ResultsFlags:
    total_results: int
    page: int
    per_page: int
    results: list['Flag']


class ResultsIdentifications:
    total_results: int
    page: int
    per_page: int
    results: list['Identification']


class ResultsIdentificationsRecentTaxa:
    total_results: int
    page: int
    per_page: int
    all_results_available: bool
    results: list[dict]


class ResultsIdentifiers:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsLanguageSearch:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsMessages:
    total_results: int
    page: int
    per_page: int
    results: list['Message']


class ResultsMessagesThread:
    total_results: int
    page: int
    per_page: int
    results: list['Message']
    thread_id: int
    flaggable_message_id: int
    reply_to_user: 'User'


class ResultsObservationFieldValues:
    total_results: int
    page: int
    per_page: int
    results: list['ObservationFieldValue']


class ResultsObservationFields:
    total_results: int
    page: int
    per_page: int
    results: list['ObservationField']


class ResultsObservationPhotos:
    total_results: int
    page: int
    per_page: int
    results: list['ObservationPhoto']


class ResultsObservationSounds:
    total_results: int
    page: int
    per_page: int
    results: list['ObservationSound']


class ResultsObservations:
    total_results: int
    total_bounds: dict
    page: int
    per_page: int
    results: list['Observation']


class ResultsObservationsDeleted:
    total_results: int
    page: int
    per_page: int
    results: list[int]


class ResultsObservationsHistogram:
    total_results: int
    page: int
    per_page: int
    results: Any


class ResultsObservationsIdentificationCategories:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsObservationsIdentifiers:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsObservationsObservers:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsObservationsPopularFieldValues:
    total_results: int
    page: int
    per_page: int
    results: list[dict]
    unannotated: dict


class ResultsObservationsQualityGrades:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsObservationsSpeciesCounts:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsObservationsUmbrellaProjectStats:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsPhotos:
    total_results: int
    page: int
    per_page: int
    results: list['Photo']


class ResultsPlaces:
    total_results: int
    page: int
    per_page: int
    results: list['Place']


class ResultsPlacesNearby:
    total_results: int
    page: int
    per_page: int
    results: dict


class ResultsProjectMembership:
    total_results: int
    page: int
    per_page: int
    results: list['ProjectMembership']


class ResultsProjectObservations:
    total_results: int
    page: int
    per_page: int
    results: list['ProjectObservation']


class ResultsProjects:
    total_results: int
    page: int
    per_page: int
    results: list['Project']


class ResultsProjectsMembers:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsProjectsPosts:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsProviderAuthorizations:
    total_results: int
    page: int
    per_page: int
    results: list['ProviderAuthorization']


class ResultsQualityMetrics:
    total_results: int
    page: int
    per_page: int
    results: list['QualityMetric']


class ResultsRelationships:
    total_results: int
    page: int
    per_page: int
    results: list['Relationship']


class SavedLocation:
    id: int
    user_id: int
    latitude: float
    longitude: float
    title: str
    positional_accuracy: int
    created_at: datetime
    updated_at: datetime
    geoprivacy: Literal['open', 'obscured', 'private']


class ResultsSavedLocations:
    total_results: int
    page: int
    per_page: int
    results: list['SavedLocation']


class ResultsSearch:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class ResultsSites:
    total_results: int
    page: int
    per_page: int
    results: list['Site']


class ResultsSounds:
    total_results: int
    page: int
    per_page: int
    results: list['Sound']


class Subscription:
    id: int
    user_id: int
    resource_type: str
    resource_id: int
    created_at: str
    updated_at: str
    taxon_id: int


class ResultsSubscriptions:
    total_results: int
    page: int
    per_page: int
    results: list['Subscription']


class ResultsTaxa:
    total_results: int
    page: int
    per_page: int
    results: list['Taxon']


class TaxonCount:
    taxon: 'Taxon'
    count: int


class ResultsTaxaCounts:
    total_results: int
    page: int
    per_page: int
    results: list['TaxonCount']


class ResultsTaxaSuggest:
    comprehensiveness: dict
    common_ancestor: 'CommonAncestor'
    results: list[dict]
    query: dict
    queryTaxon: 'Taxon'
    queryPlace: 'Place'


class TaxonIdSummary:
    id: int
    uuid: str
    active: bool
    taxon_id: int
    taxon_name: str
    taxon_common_name: str
    taxon_photo_id: int
    taxon_photo_attribution: str
    taxon_photo_observation_id: int
    taxon_group: str
    language: str
    run_name: str
    run_generated_at: datetime
    run_description: str
    created_at: datetime
    updated_at: datetime
    id_summaries: list['IdSummary']


class ResultsTaxonIdSummaries:
    total_results: int
    page: int
    per_page: int
    results: list['TaxonIdSummary']


class ResultsTaxonNamePriorities:
    total_results: int
    page: int
    per_page: int
    results: list['TaxonNamePriority']


class ResultsTaxonSummary:
    conservation_status: 'ConservationStatus'
    listed_taxon: 'ListedTaxon'
    wikipedia_summary: str


class ResultsTranslationsLocales:
    total_results: int
    page: int
    per_page: int
    results: list[dict]


class Update:
    id: int
    comment: 'Comment'
    comment_id: int
    created_at: datetime
    identification: 'Identification'
    identification_id: int
    notifier_id: int
    notifier_type: str
    notification: str
    resource_owner_id: int
    resource_type: str
    resource_id: int
    resource_uuid: str
    viewed: bool


class ResultsUpdates:
    total_results: int
    page: int
    per_page: int
    results: list['Update']


class ResultsUsers:
    total_results: int
    page: int
    per_page: int
    results: list['User']


class ResultsUsersMe:
    total_results: int
    page: int
    per_page: int
    results: list['PrivateUser']


class ResultsUsersNotificationCounts:
    updates_count: int
    messages_count: int


class UtfGrid:
    grid: list[str]
    keys: list[str]
    data: dict
