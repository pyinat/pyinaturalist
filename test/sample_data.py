"Sample responses representing different variations on all supported resource types"
# flake8: noqa: F401, F403
import json
from glob import glob
from os.path import basename, join, splitext
from typing import Dict

from pyinaturalist.constants import SAMPLE_DATA_DIR


def load_sample_data(filename):
    """Load a single sample data file"""
    with open(join(SAMPLE_DATA_DIR, filename)) as f:
        return json.load(f)


def load_all_sample_data() -> Dict[str, Dict]:
    """Load all sample data files"""
    sample_data = {}
    for file_path in glob(join(SAMPLE_DATA_DIR, '*.json')):
        name = splitext(basename(file_path))[0]
        sample_data[name] = json.load(open(file_path))
    return sample_data


# Individual JSON records from sample response data
# --------------------------------------------------

SAMPLE_DATA = load_all_sample_data()

j_observation_1 = SAMPLE_DATA['get_observation']['results'][0]
j_observation_2 = SAMPLE_DATA['get_observations_node_page1']['results'][0]
j_observation_3_ofvs = SAMPLE_DATA['get_observation_with_ofvs']['results'][0]
j_observation_4_sounds = SAMPLE_DATA['get_observation_with_sounds']
j_observation_5_annotations = SAMPLE_DATA['get_observations_by_id']['results'][0]
j_observation_identifiers = SAMPLE_DATA['get_observation_identifiers_node_page1']
j_observation_observers = SAMPLE_DATA['get_observation_observers_node_page1']
j_taxon_1 = SAMPLE_DATA['get_taxa_by_id']['results'][0]
j_taxon_2_partial = SAMPLE_DATA['get_taxa']['results'][0]
j_taxon_3_no_common_name = SAMPLE_DATA['get_taxa']['results'][2]
j_taxon_4_preferred_place = SAMPLE_DATA['get_taxa_with_preferred_place']['results'][0]
j_taxon_5_cs_status = j_observation_2['taxon']
j_taxon_6_cs_statuses = SAMPLE_DATA['get_taxa_by_id_conservation_statuses']['results'][0]
j_taxon_7_autocomplete = SAMPLE_DATA['get_taxa_autocomplete']['results'][0]
j_taxon_8_all_names = SAMPLE_DATA['get_taxa_with_all_names']['results'][0]
j_taxon_summary_1_conserved = SAMPLE_DATA['get_observation_taxon_summary_conserved']
j_taxon_summary_2_listed = SAMPLE_DATA['get_observation_taxon_summary_listed']

j_annotation_1 = j_observation_5_annotations['annotations'][0]
j_comments = j_observation_2['comments']
j_comment_1 = j_comments[0]
j_comment_2 = j_comments[1]
j_controlled_terms = SAMPLE_DATA['get_controlled_terms']['results']
j_controlled_term_1 = j_controlled_terms[0]
j_controlled_term_2 = j_controlled_terms[1]
j_controlled_term_value_1 = j_controlled_term_1['values'][0]
j_identification_1 = SAMPLE_DATA['get_identifications']['results'][0]
j_identification_2 = SAMPLE_DATA['get_identifications']['results'][1]
j_identification_3 = j_observation_2['identifications'][0]
j_life_list = SAMPLE_DATA['get_observation_taxonomy']
j_listed_taxon_1 = j_taxon_summary_2_listed['listed_taxon']
j_listed_taxon_2_partial = j_taxon_1['listed_taxa'][0]
j_message = SAMPLE_DATA['get_messages']['results'][0]
j_obs_fields = SAMPLE_DATA['get_observation_fields_page1']
j_obs_field_1 = j_obs_fields[0]
j_obs_field_2 = j_obs_fields[1]
j_obs_species_counts = SAMPLE_DATA['get_observation_species_counts']['results']
j_ofv_1_numeric = j_observation_3_ofvs['ofvs'][1]
j_ofv_2_taxon = j_observation_3_ofvs['ofvs'][0]
j_ofv_3_date = j_observation_3_ofvs['ofvs'][2]
j_ofv_4_datetime = j_observation_3_ofvs['ofvs'][3]
j_photo_1 = j_taxon_1['taxon_photos'][0]['photo']
j_photo_2_partial = j_taxon_1['default_photo']
j_place_1 = SAMPLE_DATA['get_places_by_id']['results'][1]
j_place_2 = SAMPLE_DATA['get_places_autocomplete']['results'][0]
j_places_nearby = SAMPLE_DATA['get_places_nearby']['results']
j_places_nearby['standard'] = j_places_nearby['standard'][:3]
j_places_nearby['community'] = j_places_nearby['community'][:3]
j_project_1 = SAMPLE_DATA['get_projects']['results'][0]
j_project_2 = SAMPLE_DATA['get_projects']['results'][1]
j_project_3_obs_fields = SAMPLE_DATA['get_projects_obs_fields']['results'][0]
j_project_4 = SAMPLE_DATA['get_projects_by_id']['results'][0]
j_search_results = SAMPLE_DATA['get_search']['results']
j_search_result_1_taxon = j_search_results[0]
j_search_result_2_place = j_search_results[1]
j_search_result_3_project = j_search_results[2]
j_search_result_4_user = j_search_results[3]
j_species_count_1 = SAMPLE_DATA['get_observation_species_counts']['results'][0]
j_species_count_2 = SAMPLE_DATA['get_observation_species_counts']['results'][1]
j_users = SAMPLE_DATA['get_users_autocomplete']['results']
j_user_1 = SAMPLE_DATA['get_user_by_id']['results'][0]
j_user_2_partial = j_users[0]
