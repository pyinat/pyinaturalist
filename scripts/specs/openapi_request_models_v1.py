# Auto-generated classes from OpenAPI spec
from datetime import date, datetime
from typing import Any, Literal


class PostAnnotation:
    annotation: dict


class PostComment:
    comment: dict


class PostFlag:
    flag: dict
    flag_explanation: str


class PostIdentification:
    identification: dict


class PostMessage:
    message: dict


class PostPost:
    commit: str
    post: dict


class PostObservation:
    observation: dict


class PostObservationFieldValue:
    observation_field_value: dict


class PostObservationVote:
    vote: Literal['up', 'down']
    scope: Literal['needs_id']


class PostProjectAdd:
    observation_id: int


class PostProjectObservation:
    project_id: int
    observation_id: int


class UpdateProjectObservation:
    project_observation: dict


class PostQuality:
    agree: bool


class PostVote:
    vote: Literal['up', 'down']


class PostUserUpdateSession:
    preferred_taxon_page_ancestors_shown: bool
    preferred_taxon_page_place_id: int
    preferred_taxon_page_tab: str
    prefers_skip_coarer_id_modal: bool
    prefers_hide_obs_show_annotations: bool
    prefers_hide_obs_show_projects: bool
    prefers_hide_obs_show_tags: bool
    prefers_hide_obs_show_observation_fields: bool
    prefers_hide_obs_show_identifiers: bool
    prefers_hide_obs_show_copyright: bool
    prefers_hide_obs_show_quality_metrics: bool


class PutFlag:
    flag: dict
