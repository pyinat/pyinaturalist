"""Things to test for each model:

* Load with sample response JSON, make sure it doesn't explode
   * Test with responses from different endpoints and/or response variations, if applicable
* Initialize the model with no args, and expect sane defaults
* Any data type conversions that run on init
* Any additional properties or aliases on the model
* Formatting in the model's __str__ method
"""
import pytest
from datetime import datetime
from dateutil.tz import tzoffset, tzutc

from pyinaturalist.constants import ICONIC_TAXA, INAT_BASE_URL, PHOTO_INFO_BASE_URL, PHOTO_SIZES
from pyinaturalist.models import (
    ID,
    OFV,
    Annotation,
    Comment,
    ControlledTerm,
    ControlledTermValue,
    LifeList,
    LifeListTaxon,
    Observation,
    ObservationField,
    Photo,
    Place,
    Project,
    ProjectObservation,
    ProjectObservationField,
    ProjectUser,
    SearchResult,
    Taxon,
    TaxonCounts,
    User,
)
from pyinaturalist.models.observation_field import ObservationFieldValue
from pyinaturalist.models.taxon import TaxonCount
from test.conftest import load_sample_data, sample_data_path

controlled_term_json = load_sample_data('get_controlled_terms.json')['results'][0]
obs_json = load_sample_data('get_observations_node_page1.json')['results'][0]
obs_json_ofvs = load_sample_data('get_observation_with_ofvs.json')['results'][0]
obs_field_json = load_sample_data('get_observation_fields_page1.json')[0]
obs_species_counts_json = load_sample_data('get_observation_species_counts.json')['results']
obs_taxonomy_json = load_sample_data('get_observation_taxonomy.json')
place_json = load_sample_data('get_places_by_id.json')['results'][0]
places_nearby_json = load_sample_data('get_places_nearby.json')['results']
project_json = load_sample_data('get_projects.json')['results'][0]
project_json_obs_fields = load_sample_data('get_projects_obs_fields.json')['results'][0]
user_json = load_sample_data('get_user_by_id.json')['results'][0]
user_json_partial = load_sample_data('get_users_autocomplete.json')['results'][0]
search_results_json = load_sample_data('get_search.json')['results']
taxon_json = load_sample_data('get_taxa_by_id.json')['results'][0]
taxon_json_partial = load_sample_data('get_taxa.json')['results'][0]

annotation_json = obs_json_ofvs['annotations'][0]
comment_json = obs_json['comments'][0]
controlled_term_value_json = controlled_term_json['values'][0]
identification_json = obs_json['identifications'][0]
ofv_json_numeric = obs_json_ofvs['ofvs'][1]
ofv_json_taxon = obs_json_ofvs['ofvs'][0]
photo_json = taxon_json['taxon_photos'][0]
photo_json = taxon_json['default_photo']
search_result_json_taxon = search_results_json[0]
search_result_json_place = search_results_json[1]
search_result_json_project = search_results_json[2]
search_result_json_user = search_results_json[3]

# Base
# --------------------


# TODO
def test_from_json():
    pass


def test_from_json_file():
    obs_list = Observation.from_json_file(sample_data_path('get_observations_node_page1.json'))
    assert isinstance(obs_list, list)
    assert isinstance(obs_list[0], Observation)
    assert obs_list[0].id == 57754375


# TODO
def test_from_json_list():
    pass


# Controlled Terms
# --------------------


def test_annotation__converters():
    annotation = Annotation.from_json(annotation_json)
    assert isinstance(annotation.user, User) and annotation.user.id == 2115051


def test_annotation__empty():
    annotation = Annotation()
    assert annotation.votes == []
    assert annotation.user is None


def test_annotation__values():
    annotation = Annotation.from_json(annotation_json)
    assert annotation.values == ['1', '2']


def test_annotation__str():
    annotation = Annotation.from_json(annotation_json)
    assert str(annotation) == '[1] 1|2 (0 votes)'


def test_controlled_term__converters():
    controlled_term = ControlledTerm.from_json(controlled_term_json)
    value = controlled_term.values[0]
    assert controlled_term.taxon_ids == [47126]
    assert isinstance(value, ControlledTermValue) and value.id == 21


def test_controlled_term__empty():
    controlled_term = ControlledTerm()
    assert controlled_term.taxon_ids == []
    assert controlled_term.values == []


def test_controlled_term__properties():
    controlled_term = ControlledTerm.from_json(controlled_term_json)
    assert (
        controlled_term.value_labels == 'No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


def test_controlled_term__str():
    controlled_term = ControlledTerm.from_json(controlled_term_json)
    assert (
        str(controlled_term)
        == '[12] Plant Phenology: No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


def test_controlled_term__value():
    controlled_term_value = ControlledTermValue.from_json(controlled_term_value_json)
    assert controlled_term_value.taxon_ids == [47125]
    assert str(controlled_term_value) == '[21] No Evidence of Flowering'


# Comments
# --------------------


def test_comment__converters():
    comment = Comment.from_json(comment_json)
    assert isinstance(comment.user, User) and comment.user.id == 2852555


def test_comment__empty():
    comment = Comment()
    assert isinstance(comment.created_at, datetime)
    assert comment.user is None


def test_comment__str():
    comment = Comment.from_json(comment_json)
    assert str(comment) == 'samroom at 2020-08-28 12:04:18+00:00: Thankyou '


# Identifications
# --------------------


def test_identification__converters():
    identification = ID.from_json(identification_json)
    assert isinstance(identification.user, User) and identification.user.id == 2852555


def test_identification__empty():
    identification = ID()
    assert isinstance(identification.created_at, datetime)
    assert identification.taxon is None
    assert identification.user is None


def test_identification__str():
    identification = ID.from_json(identification_json)
    assert str(identification) == (
        '[126501311] Species: Danaus plexippus (Monarch) (improving) added on '
        '2020-08-27 13:00:51-05:00 by samroom'
    )


# Life Lists
# --------------------


def test_life_list__converters():
    life_list = LifeList.from_json(obs_taxonomy_json)
    assert life_list.taxa[0] == life_list[0]
    assert len(life_list) == 9
    assert isinstance(life_list.taxa[0], LifeListTaxon) and life_list.taxa[0].id == 1


def test_life_list__empty():
    life_list = LifeList()
    life_list.taxa == []
    life_list._taxon_counts is None


def test_life_list__count():
    life_list = LifeList.from_json(obs_taxonomy_json)
    assert life_list.count(1) == 3023  # Animalia
    assert life_list.count(981) == 2  # Phasianus colchicus
    assert life_list.count(-1) == 4  # Observations with no taxon
    assert life_list.count(9999999) == 0  # Unobserved taxon


# Observations
# --------------------


def test_observation__converters():
    obs = Observation.from_json(obs_json)
    utc = tzoffset('Etc/UTC', 0)
    assert obs.created_at == datetime(2020, 8, 27, 0, 0, tzinfo=utc)
    assert obs.observed_on == datetime(2020, 8, 27, 8, 57, 22, tzinfo=utc)

    assert isinstance(obs.comments[0], Comment) and obs.comments[0].id == 5326888
    assert isinstance(obs.identifications[0], ID) and obs.identifications[0].id == 126501311
    assert isinstance(obs.photos[0], Photo) and obs.photos[0].id == 92152429
    assert isinstance(obs.taxon, Taxon) and obs.taxon.id == 48662
    assert isinstance(obs.user, User) and obs.user.id == 2852555

    assert obs.location == (50.0949055, -104.71929167)


def test_observation__empty():
    obs = Observation()
    assert isinstance(obs.created_at, datetime)
    assert obs.comments == []
    assert obs.identifications == []
    assert obs.photos == []
    assert obs.uuid is None
    assert obs.taxon is None
    assert obs.user is None


def test_observation__with_ofvs():
    obs = Observation.from_json(obs_json_ofvs)
    ofv = obs.ofvs[0]
    assert isinstance(ofv, ObservationFieldValue)
    assert ofv.id == 14106828
    assert ofv.user.id == 2115051


def test_observation__project_observations_():
    obs = Observation.from_json(obs_json_ofvs)
    proj_obs = obs.project_observations[0]
    assert isinstance(proj_obs, ProjectObservation) and proj_obs.id == 48899479


def test_observation__thumbnail_url():
    obs = Observation.from_json(obs_json)
    assert obs.thumbnail_url == 'https://static.inaturalist.org/photos/92152429/square.jpg?1598551272'


# Observation Fields
# --------------------


def test_observation_field__converters():
    obs_field = ObservationField.from_json(obs_field_json)
    assert obs_field.allowed_values == ['Male', 'Female', 'Unknown']
    assert obs_field.created_at == datetime(2016, 5, 29, 16, 17, 8, 51000, tzinfo=tzutc())


def test_observation_field__empty():
    obs_field = ObservationField()
    assert obs_field.allowed_values == []
    assert isinstance(obs_field.created_at, datetime)


def test_observation_field__str():
    obs_field = ObservationField.from_json(obs_field_json)
    assert str(obs_field) == '[4813] Sex (deer/turkey) (text)'


def test_observation_field_value__converters():
    ofv = OFV.from_json(ofv_json_numeric)
    assert ofv.datatype == 'numeric'
    assert ofv.value == 100
    assert ofv.taxon is None
    assert isinstance(ofv.user, User) and ofv.user.id == 2115051


def test_observation_field_value__taxon():
    ofv = OFV.from_json(ofv_json_taxon)
    assert ofv.datatype == 'taxon'
    assert ofv.value == 119900
    assert isinstance(ofv.taxon, Taxon) and ofv.taxon.id == 119900


def test_observation_field_value__empty():
    ofv = OFV()
    assert ofv.value is None
    assert ofv.taxon is None


def test_observation_field_value__str():
    ofv = OFV.from_json(ofv_json_taxon)
    assert str(ofv) == 'Feeding on: 119900'


# Photos
# --------------------


def test_photo__converters():
    photo = Photo.from_json(photo_json)
    assert photo.id == 38359335
    assert photo.license_code == 'CC-BY-NC'
    assert photo.original_dimensions == (2048, 1365)
    assert photo.info_url == f'{PHOTO_INFO_BASE_URL}/38359335'


def test_photo__empty():
    photo = Photo()
    assert photo.original_dimensions == (0, 0)


def test_photo__license():
    photo = Photo.from_json(photo_json)
    assert photo.has_cc_license is True
    photo.license_code = 'CC0'
    assert photo.has_cc_license is True

    photo.license_code = None
    assert photo.has_cc_license is False
    photo.license_code = 'all rights reserved'
    assert photo.has_cc_license is False


@pytest.mark.parametrize('size', PHOTO_SIZES)
def test_photo__urls(size):
    photo = Photo.from_json(photo_json)
    assert (
        photo.url_size(size)
        == getattr(photo, f'{size}_url')
        == f'https://static.inaturalist.org/photos/38359335/{size}.jpg?1557348751'
    )
    assert photo.url_size('embiggened') is None


def test_photo__str():
    photo = Photo.from_json(photo_json)
    assert str(photo) == (
        '[38359335] https://static.inaturalist.org/photos/38359335/original.jpg?1557348751 '
        '(CC-BY-NC, 2048x1365)'
    )


# Places
# --------------------


def test_place__converters():
    place = Place.from_json(place_json)
    assert place.category is None
    assert place.location == (-29.665119, 17.88583)


def test_place__empty():
    place = Place()
    assert place.ancestor_place_ids == []
    assert place.bounding_box_geojson == {}
    assert place.geometry_geojson == {}


def test_places__nearby():
    """Results from /places/nearby should have an extra 'category' attribute"""
    places = Place.from_json_list(places_nearby_json)
    assert places[0].category == 'standard'
    assert places[-1].category == 'community'


# Projects
# --------------------


def test_project__converters():
    project = Project.from_json(project_json)
    assert project.location == (48.777404, -122.306929)
    assert project.project_observation_rules == project.obs_rules
    assert project.obs_rules[0]['id'] == 616862
    assert project.search_parameters[0]['field'] == 'quality_grade'
    assert project.user_ids[-1] == 3387092 and len(project.user_ids) == 33

    admin = project.admins[0]
    assert isinstance(admin, ProjectUser) and admin.id == 233188 and admin.role == 'manager'
    assert isinstance(project.user, User) and project.user.id == 233188


def test_project__empty():
    project = Project()
    assert project.admins == []
    assert isinstance(project.created_at, datetime)
    assert project.location is None
    assert project.project_observation_rules == []
    assert project.search_parameters == []
    assert project.user is None


def test_project__with_obs_fields():
    project = Project.from_json(project_json_obs_fields)
    obs_field = project.project_observation_fields[0]
    assert isinstance(obs_field, ProjectObservationField)
    assert obs_field.id == 30
    assert obs_field.position == 0
    assert obs_field.required is False


# Search
# --------------------


def test_search__empty():
    search_result = SearchResult()
    assert search_result.score == 0
    assert search_result.matches == []
    assert search_result.record is None


def test_search__place():
    search_result = SearchResult.from_json(search_result_json_place)
    assert search_result.score == 7.116488
    assert isinstance(search_result.record, Place) and search_result.record.id == 113562


def test_search__project():
    search_result = SearchResult.from_json(search_result_json_project)
    assert search_result.score == 6.9390197
    assert isinstance(search_result.record, Project) and search_result.record.id == 9978


def test_search__taxon():
    search_result = SearchResult.from_json(search_result_json_taxon)
    assert search_result.score == 9.062307
    assert isinstance(search_result.record, Taxon) and search_result.record.id == 47792


def test_search__user():
    search_result = SearchResult.from_json(search_result_json_user)
    assert search_result.score == 4.6454225
    assert isinstance(search_result.record, User) and search_result.record.id == 113886


# Taxa
# --------------------


def test_taxon__converters():
    taxon = Taxon.from_json(taxon_json_partial)
    assert isinstance(taxon.default_photo, Photo) and taxon.default_photo.id == 38359335


def test_taxon__empty():
    taxon = Taxon()
    assert taxon.preferred_common_name == ''
    assert taxon.ancestors == []
    assert taxon.children == []
    assert taxon.default_photo is None
    assert taxon.taxon_photos == []


def test_taxon__taxonomy():
    taxon = Taxon.from_json(taxon_json)
    parent = taxon.ancestors[0]
    child = taxon.children[0]
    assert isinstance(parent, Taxon) and parent.id == 1
    assert isinstance(child, Taxon) and child.id == 70115


def test_taxon__properties():
    taxon = Taxon.from_json(taxon_json)
    assert taxon.url == f'{INAT_BASE_URL}/taxa/70118'
    assert taxon.ancestry.startswith('Animalia | Arthropoda | Hexapoda | ')
    assert isinstance(taxon.parent, Taxon) and taxon.parent.id == 53850


@pytest.mark.parametrize('taxon_id', ICONIC_TAXA.keys())
def test_taxon__emoji(taxon_id):
    taxon = Taxon(iconic_taxon_id=taxon_id)
    assert taxon.emoji is not None


@pytest.mark.parametrize('taxon_name', ICONIC_TAXA.values())
def test_taxon__icon_url(taxon_name):
    taxon = Taxon(iconic_taxon_name=taxon_name)
    assert taxon.icon_url is not None


def test_taxon_properties__partial():
    taxon = Taxon.from_json(taxon_json_partial)
    assert taxon.ancestry.startswith('48460 | 1 | 47120 | ')
    assert taxon.parent is None


# TODO
def test_taxon__update_from_full_record():
    pass


def test_taxon_counts__converters():
    taxon_counts = TaxonCounts.from_json(obs_species_counts_json)
    assert taxon_counts.taxa[0] == taxon_counts[0]
    assert len(taxon_counts) == 9
    assert isinstance(taxon_counts.taxa[0], TaxonCount) and taxon_counts.taxa[0].count == 31


def test_taxon_counts__empty():
    taxon_counts = TaxonCounts()
    assert taxon_counts.taxa == []


# Users
# --------------------


def test_user__converters():
    user = User.from_json(user_json)
    assert user.identifications_count == 95624


def test_user__empty():
    user = User()
    assert isinstance(user.created_at, datetime)
    assert user.roles == []


def test_user__partial():
    user = User.from_json(user_json_partial)
    assert user.id == 886482
    assert user.name == 'Nicolas Noé'


def test_user__properties():
    user = User.from_json(user_json)
    assert user.username == user.login == 'kueda'
    assert user.display_name == user.name == 'Ken-ichi Ueda'


def test_user__str():
    user = User.from_json(user_json)
    assert str(user) == '[1] kueda (Ken-ichi Ueda)'
