# Auto-generated classes from OpenAPI spec
from datetime import date, datetime
from typing import Any, Literal


class AnnotationsCreate:
    resource_type: str
    resource_id: str
    controlled_attribute_id: int
    controlled_value_id: int


class CommentsCreate:
    fields: Any
    comment: dict


class CommentsUpdate:
    fields: Any
    comment: dict


class ComputervisionScoreImage:
    fields: Any
    image: bytes


class FlagsCreate:
    flag: dict
    flag_explanation: str
    fields: Any


class FlagsUpdate:
    flag: dict
    fields: Any


class IdentificationsCreate:
    fields: Any
    identification: dict


class IdentificationsUpdate:
    fields: Any
    identification: dict


class MessagesCreate:
    message: dict
    fields: Any


class ObservationFieldValuesCreate:
    fields: Any
    observation_field_value: dict


class ObservationPhotosCreate:
    fields: Any
    observation_photo: dict


class ObservationPhotosCreateMultipart:
    fields: Any
    observation_photo[observation_id]: str
    observation_photo[uuid]: str
    observation_photo[position]: int
    file: bytes


class ObservationPhotosUpdate:
    fields: Any
    observation_photo: dict


class ObservationSoundsCreate:
    fields: Any
    observation_sound: dict


class ObservationSoundsCreateMultipart:
    fields: Any
    observation_sound[observation_id]: str
    file: bytes


class ObservationSoundsUpdate:
    fields: Any
    observation_sound: dict


class ObservationsCreate:
    fields: Any
    observation: dict


class ObservationsUpdate:
    fields: Any
    ignore_photos: bool
    observation: dict


class PhotosCreate:
    file: bytes
    fields: Any
    uuid: str


class ProjectObservationsCreate:
    fields: Any
    project_observation: dict


class ProjectObservationsUpdate:
    fields: Any
    project_observation: dict


class ProjectUsersUpdate:
    project_user: dict


class ProjectsFeature:
    inat_site_id: int
    noteworthy: bool


class ProjectsUnfeature:
    inat_site_id: int


class RelationshipsCreate:
    fields: Any
    relationship: dict


class RelationshipsUpdate:
    fields: Any
    relationship: dict


class SavedLocationsCreate:
    fields: Any
    saved_location: dict


class TaxonNamePrioritiesCreate:
    fields: Any
    taxon_name_priority: dict


class TaxonNamePrioritiesUpdate:
    fields: Any
    taxon_name_priority: dict


class UsersResetPassword:
    user: dict


class UsersUpdate:
    user: dict
    icon_delete: bool


class UsersUpdateMultipart:
    user[data_transfer_consent]: bool
    user[description]: str
    user[faved_project_ids]: list[float]
    user[email]: str
    user[locale]: str
    user[login]: str
    user[make_observation_licenses_same]: bool
    user[make_photo_licenses_same]: bool
    user[make_sound_licenses_same]: bool
    user[name]: str
    user[pi_consent]: bool
    user[place_id]: int
    user[preferred_observation_fields_by]: str
    user[preferred_observation_license]: str
    user[preferred_photo_license]: str
    user[preferred_project_addition_by]: str
    user[preferred_sound_license]: str
    user[prefers_automatic_taxonomic_changes]: bool
    user[prefers_comment_email_notification]: bool
    user[prefers_common_names]: bool
    user[prefers_community_taxa]: bool
    user[prefers_identification_email_notification]: bool
    user[prefers_infraspecies_identification_notifications]: bool
    user[prefers_mention_email_notification]: bool
    user[prefers_message_email_notification]: bool
    user[prefers_monthly_supporter_badge]: bool
    user[prefers_no_email]: bool
    user[prefers_no_tracking]: bool
    user[prefers_non_disagreeing_identification_notifications]: bool
    user[prefers_project_added_your_observation_email_notification]: bool
    user[prefers_project_curator_change_email_notification]: bool
    user[prefers_project_journal_post_email_notification]: bool
    user[prefers_receive_mentions]: bool
    user[prefers_redundant_identification_notifications]: bool
    user[prefers_scientific_name_first]: bool
    user[prefers_taxon_change_email_notification]: bool
    user[prefers_taxon_or_place_observation_email_notification]: bool
    user[prefers_user_observation_email_notification]: bool
    user[search_place_id]: int
    user[site_id]: int
    user[time_zone]: str
    user[password]: str
    user[password_confirmation]: str
    icon_delete: bool
    user[icon]: bytes
