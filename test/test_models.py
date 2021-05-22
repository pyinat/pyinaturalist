from datetime import datetime
from dateutil.tz import tzoffset, tzutc

from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.models import (
    ID,
    OFV,
    Comment,
    Observation,
    ObservationField,
    Photo,
    Place,
    Project,
    ProjectObservationField,
    ProjectUser,
    Taxon,
    User,
)
from test.conftest import load_sample_data

obs_json = load_sample_data('get_observations_node_page1.json')['results'][0]
obs_field_json = load_sample_data('get_observation_fields_page1.json')[0]
ofv_json_taxon = load_sample_data('get_observation_with_ofvs.json')['results'][0]['ofvs'][0]
ofv_json_numeric = load_sample_data('get_observation_with_ofvs.json')['results'][0]['ofvs'][1]
place_json = load_sample_data('get_places_by_id.json')['results'][0]
places_nearby_json = load_sample_data('get_places_nearby.json')['results']
project_json = load_sample_data('get_projects.json')['results'][0]
project_json_obs_fields = load_sample_data('get_projects_obs_fields.json')['results'][0]
user_json = load_sample_data('get_user_by_id.json')['results'][0]
user_json_partial = load_sample_data('get_users_autocomplete.json')['results'][0]
taxon_json = load_sample_data('get_taxa_by_id.json')['results'][0]
taxon_json_partial = load_sample_data('get_taxa.json')['results'][0]

comment_json = obs_json['comments'][0]
identification_json = obs_json['identifications'][0]
photo_json = taxon_json['taxon_photos'][0]
photo_json = taxon_json['default_photo']


# Comments
# --------------------


def test_comment_converters():
    """Test data type conversions"""
    comment = Comment.from_json(comment_json)
    assert isinstance(comment.user, User) and comment.user.id == 2852555


def test_comment_empty():
    """We should be able to initialize the model with no args, and get sane defaults"""
    comment = Comment()
    assert isinstance(comment.created_at, datetime)
    assert comment.user is None


# Identifications
# --------------------


def test_identification_converters():
    identification = ID.from_json(identification_json)
    assert isinstance(identification.user, User) and identification.user.id == 2852555


def test_identification_empty():
    identification = ID()
    assert isinstance(identification.created_at, datetime)
    assert identification.taxon is None
    assert identification.user is None


# Observations
# --------------------


def test_observation_converters():
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


def test_observation_empty():
    obs = Observation()
    assert isinstance(obs.created_at, datetime)
    assert obs.comments == []
    assert obs.identifications == []
    assert obs.photos == []
    assert obs.uuid is None
    assert obs.taxon is None
    assert obs.user is None


def test_observation_thumbnail_url():
    obs = Observation.from_json(obs_json)
    assert obs.thumbnail_url == 'https://static.inaturalist.org/photos/92152429/square.jpg?1598551272'


# Observation Fields
# --------------------


def test_observation_field_converters():
    obs_field = ObservationField.from_json(obs_field_json)
    assert obs_field.allowed_values == ['Male', 'Female', 'Unknown']
    assert obs_field.created_at == datetime(2016, 5, 29, 16, 17, 8, 51000, tzinfo=tzutc())


def test_observation_field_empty():
    obs_field = ObservationField()
    assert obs_field.allowed_values == []
    assert isinstance(obs_field.created_at, datetime)


def test_observation_field_value_converters():
    ofv = OFV.from_json(ofv_json_numeric)
    assert ofv.datatype == 'numeric'
    assert ofv.value == 100
    assert ofv.taxon is None
    assert isinstance(ofv.user, User) and ofv.user.id == 2115051


def test_observation_field_value_taxon():
    ofv = OFV.from_json(ofv_json_taxon)
    assert ofv.datatype == 'taxon'
    assert ofv.value == 119900
    assert isinstance(ofv.taxon, Taxon) and ofv.taxon.id == 119900


def test_observation_field_value_empty():
    ofv = OFV()
    assert ofv.value is None
    assert ofv.taxon is None


# Photos
# --------------------


def test_photo_converters():
    photo = Photo.from_json(photo_json)
    assert photo.license_code == 'CC-BY-NC'
    assert photo.original_dimensions == (2048, 1365)


def test_photo_empty():
    photo = Photo()
    assert photo.original_dimensions == (0, 0)


# TODO
def test_photo_urls():
    pass


# Places
# --------------------


def test_place_converters():
    place = Place.from_json(place_json)
    assert place.location == (-29.665119, 17.88583)


def test_place_empty():
    place = Place()
    assert place.ancestor_place_ids == []
    assert place.bounding_box_geojson == {}
    assert place.geometry_geojson == {}


# TODO
def test_place_from_json_list():
    pass


# Projects
# --------------------


def test_project_converters():
    project = Project.from_json(project_json)
    assert project.location == (48.777404, -122.306929)
    assert project.project_observation_rules == project.obs_rules
    assert project.obs_rules[0]['id'] == 616862
    assert project.search_parameters[0]['field'] == 'quality_grade'
    assert project.user_ids[-1] == 3387092 and len(project.user_ids) == 33

    admin = project.admins[0]
    assert isinstance(admin, ProjectUser) and admin.id == 233188 and admin.role == 'manager'
    assert isinstance(project.user, User) and project.user.id == 233188


def test_project_with_obs_fields():
    project = Project.from_json(project_json_obs_fields)
    obs_field = project.project_observation_fields[0]
    assert isinstance(obs_field, ProjectObservationField)
    assert obs_field.id == 30
    assert obs_field.position == 0
    assert obs_field.required is False


def test_project_empty():
    project = Project()
    assert project.admins == []
    assert isinstance(project.created_at, datetime)
    assert project.location is None
    assert project.project_observation_rules == []
    assert project.search_parameters == []
    assert project.user is None


# Taxa
# --------------------


def test_taxon_converters():
    taxon = Taxon.from_json(taxon_json_partial)
    assert isinstance(taxon.default_photo, Photo) and taxon.default_photo.id == 38359335


def test_taxon_empty():
    taxon = Taxon()
    assert taxon.preferred_common_name == ''
    assert taxon.ancestors == []
    assert taxon.children == []
    assert taxon.default_photo is None
    assert taxon.taxon_photos == []


def test_taxon_taxonomy():
    taxon = Taxon.from_json(taxon_json)
    parent = taxon.ancestors[0]
    child = taxon.children[0]
    assert isinstance(parent, Taxon) and parent.id == 1
    assert isinstance(child, Taxon) and child.id == 70115


def test_taxon_properties():
    taxon = Taxon.from_json(taxon_json)
    assert taxon.ancestry.startswith('Animalia | Arthropoda | Hexapoda | ')
    assert taxon.url == f'{API_V1_BASE_URL}/taxa/70118'


# TODO
def test_update_from_full_record():
    pass


# Users
# --------------------


def test_user_converters():
    user = User.from_json(user_json)
    assert user.identifications_count == 95624


def test_user_empty():
    user = User()
    assert isinstance(user.created_at, datetime)
    assert user.roles == []


def test_user_partial():
    user = User.from_json(user_json_partial)
    assert user.id == 886482
    assert user.name == 'Nicolas Noé'


def test_user_aliases():
    user = User.from_json(user_json)
    assert user.username == user.login == 'kueda'
    assert user.display_name == user.name == 'Ken-ichi Ueda'
