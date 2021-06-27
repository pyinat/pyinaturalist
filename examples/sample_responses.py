"Get sample responses of every type to experiment with"
# flake8: noqa: F401, F403
import json
from os.path import join

from pyinaturalist import *
from pyinaturalist.constants import SAMPLE_DATA_DIR
from pyinaturalist.formatters import format_table, pprint
from pyinaturalist.models import (
    Annotation,
    Comment,
    ControlledTerm,
    Identification,
    Observation,
    ObservationField,
    ObservationFieldValue,
    Photo,
    Place,
    Project,
    SearchResult,
    Taxon,
    User,
)


def load_sample_data(filename):
    with open(join(SAMPLE_DATA_DIR, filename)) as f:
        return json.load(f)


# Sample JSON
controlled_term_json = load_sample_data('get_controlled_terms.json')['results']
obs_json = load_sample_data('get_observations_node_page1.json')['results'][0]
obs_json_ofvs = load_sample_data('get_observation_with_ofvs.json')['results'][0]
obs_fields_json = load_sample_data('get_observation_fields_page1.json')
obs_taxonomy_json = load_sample_data('get_observation_taxonomy.json')
place_json = load_sample_data('get_places_by_id.json')['results'][0]
places_nearby_json = load_sample_data('get_places_nearby.json')['results']
project_json = load_sample_data('get_projects_obs_fields.json')['results'][0]
search_json = load_sample_data('get_search.json')
user_json = load_sample_data('get_user_by_id.json')['results'][0]
user_json_autocomplete = load_sample_data('get_users_autocomplete.json')['results']
taxon_json = load_sample_data('get_taxa_by_id.json')['results'][0]
taxon_json_partial = load_sample_data('get_taxa.json')['results'][0]
annotation_json = obs_json_ofvs['annotations'][0]
comment_json = obs_json['comments'][0]
controlled_term_value_json = controlled_term_json[0]['values']
identification_json = obs_json['identifications'][0]
obs_field_json = obs_fields_json[0]
ofv_json_numeric = obs_json_ofvs['ofvs'][1]
ofv_json_taxon = obs_json_ofvs['ofvs'][0]
photo_json = taxon_json['taxon_photos'][0]['photo']
photo_json_partial = taxon_json['default_photo']
search_results_json = load_sample_data('get_search.json')['results']
user_json_partial = user_json_autocomplete[0]

# Sample model objects
annotation = Annotation.from_json(annotation_json)
comment = Comment.from_json(comment_json)
controlled_term = ControlledTerm.from_json(controlled_term_json[0])
identification = Identification.from_json(identification_json)
life_list = LifeList.from_json(obs_taxonomy_json)
observation = Observation.from_json(obs_json)
observation_with_ofvs = Observation.from_json(obs_json_ofvs)
observation_field = ObservationField.from_json(obs_field_json)
ofv = ObservationFieldValue.from_json(ofv_json_numeric)
photo = Photo.from_json(photo_json)
photo_partial = Photo.from_json(photo_json_partial)
place = Place.from_json(place_json)
places_nearby = Place.from_json_list(places_nearby_json)
project = Project.from_json(project_json)
search_results = SearchResult.from_json_list(search_results_json)
taxon = Taxon.from_json(taxon_json)
taxon_partial = Taxon.from_json(taxon_json_partial)
user = User.from_json(user_json)

# Sample tables
annotation_table = format_table(observation_with_ofvs.annotations)
comment_table = format_table(observation.comments)
controlled_term_table = format_table(ControlledTerm.from_json_list(controlled_term_json))
identification_table = format_table(observation.identifications)
life_list_table = format_table(life_list)
observation_table = format_table([observation, observation_with_ofvs])
obs_field_table = format_table(ObservationField.from_json_list(obs_fields_json))
ofv_table = format_table(observation_with_ofvs.ofvs)
photo_table = format_table([photo, photo_partial, observation.photos[0]])
place_table = format_table(places_nearby)
project_table = format_table([project, project, project])
search_results_table = format_table(search_results)
taxon_table = format_table([taxon, observation_with_ofvs.taxon, observation.taxon])
user_table = format_table(User.from_json_list(user_json_autocomplete))
