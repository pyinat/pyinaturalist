"Get sample response JSON and model objects of every type to experiment with"
# flake8: noqa: F401, F403
import json
from os.path import join

from pyinaturalist import *
from pyinaturalist.constants import SAMPLE_DATA_DIR
from pyinaturalist.models import (
    Annotation,
    Comment,
    Identification,
    Observation,
    ObservationField,
    ObservationFieldValue,
    Photo,
    Place,
    Project,
    Taxon,
    User,
)

# Get colorized/formatted output, if `rich` is installed
try:
    from rich import pretty

    pretty.install()
except ImportError:
    pass


def load_sample_data(filename):
    with open(join(SAMPLE_DATA_DIR, filename)) as f:
        return json.load(f)


# Sample JSON
obs_json = load_sample_data('get_observations_node_page1.json')['results'][0]
obs_json_ofvs = load_sample_data('get_observation_with_ofvs.json')['results'][0]
obs_field_json = load_sample_data('get_observation_fields_page1.json')[0]
obs_taxonomy_json = load_sample_data('get_observation_taxonomy.json')
place_json = load_sample_data('get_places_by_id.json')['results'][0]
places_nearby_json = load_sample_data('get_places_nearby.json')['results']
project_json = load_sample_data('get_projects_obs_fields.json')['results'][0]
user_json = load_sample_data('get_user_by_id.json')['results'][0]
user_json_partial = load_sample_data('get_users_autocomplete.json')['results'][0]
taxon_json = load_sample_data('get_taxa_by_id.json')['results'][0]
taxon_json_partial = load_sample_data('get_taxa.json')['results'][0]

annotation_json = obs_json_ofvs['annotations'][0]
comment_json = obs_json['comments'][0]
identification_json = obs_json['identifications'][0]
ofv_json_numeric = obs_json_ofvs['ofvs'][1]
ofv_json_taxon = obs_json_ofvs['ofvs'][0]
photo_json = taxon_json['taxon_photos'][0]
photo_json = taxon_json['default_photo']

# Sample model objects
annotation = Annotation.from_json(annotation_json)
comment = Comment.from_json(comment_json)
identification = Identification.from_json(identification_json)
life_list = LifeList.from_taxonomy_json(obs_taxonomy_json)
observation = Observation.from_json(obs_json)
observation_with_ofvs = Observation.from_json(obs_json_ofvs)
observation_field = ObservationField.from_json(obs_field_json)
ofv = ObservationFieldValue.from_json(ofv_json_numeric)
photo = Photo.from_json(photo_json)
place = Place.from_json(place_json)
project = Project.from_json(project_json)
taxon_partial = Taxon.from_json(taxon_json_partial)
taxon = Taxon.from_json(taxon_json)
user = User.from_json(user_json)
