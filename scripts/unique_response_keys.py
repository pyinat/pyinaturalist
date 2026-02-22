#!/usr/bin/env python
# ruff: noqa: E402, F401, F402, F403, F405
"""A script used to determine unique response keys for each response type"""

import sys
from itertools import chain
from pprint import pprint

from pyinaturalist.constants import PROJECT_DIR

sys.path.insert(0, str(PROJECT_DIR))
from test.sample_data import *

RESPONSES = {
    'annotation': j_annotation_1,
    'comment': j_comment_1,
    'controlled_term': j_controlled_term_1,
    'controlled_term_value': j_controlled_term_value_1,
    'identification': j_identification_1,
    'observation_field': j_obs_field_1,
    'observation': j_observation_1,
    'life_list': j_life_list_1,
    'observation_field_value': j_ofv_1_numeric,
    'photo': j_photo_1,
    'place': j_place_1,
    'places_nearby': j_places_nearby,
    'project': j_project_1,
    'search': j_search_results[0],
    'taxon': j_taxon_2_partial,
    'taxon_counts': j_obs_species_counts[0],
    'user': j_user_2_partial,
}


def get_unique_keys(response_type):
    keys = set(RESPONSES[response_type].keys())
    other_responses = [v for k, v in RESPONSES.items() if k != response_type]
    other_keys = set(chain.from_iterable([x.keys() for x in other_responses]))
    return sorted(keys - other_keys)


if __name__ == '__main__':
    for k in RESPONSES:
        print(f'{k}: ', end='')
        pprint(get_unique_keys(k))
