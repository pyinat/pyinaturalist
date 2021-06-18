#!/usr/bin/env python
# flake8: noqa: F401, F402, F403, F405
"""A script used to determine unique response keys for each response type"""
import sys
from itertools import chain

sys.path.insert(0, '../examples')
from examples.sample_responses import *

RESPONSES = {
    'annotation': annotation_json,
    'comment': comment_json,
    'identification': identification_json,
    'observation_field': obs_field_json,
    'observation': obs_json,
    'life_list': obs_taxonomy_json,
    'observation_field_value': ofv_json_numeric,
    'photo': photo_json_partial,
    'place': place_json,
    'places_nearby': places_nearby_json,
    'project': project_json,
    'search': search_results_json[0],
    'taxon': taxon_json_partial,
    'user': user_json_partial,
}


def get_unique_keys(response_type):
    keys = set(RESPONSES[response_type].keys())
    other_responses = [v for k, v in RESPONSES.items() if k != response_type]
    other_keys = set(chain.from_iterable([x.keys() for x in other_responses]))
    return sorted(keys - other_keys)


if __name__ == '__main__':
    print({k: get_unique_keys(k) for k in RESPONSES})
