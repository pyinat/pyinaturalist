#!/usr/bin/env python
# flake8: noqa: F401, F403
"""Sample response data of every type to experiment with"""
import sys

from rich import print

from pyinaturalist import PROJECT_DIR, format_table, pprint
from pyinaturalist.models import *

# Import sample response JSON used for unit tests
sys.path.insert(0, PROJECT_DIR)
from test.sample_data import *

# Sample model objects
annotation = Annotation.from_json(j_annotation_1)
comment = Comment.from_json(j_comment_1)
controlled_term = ControlledTerm.from_json(j_controlled_term_1)
identification = Identification.from_json(j_identification_1)
life_list = LifeList.from_json(j_life_list)
observation = Observation.from_json(j_observation_1)
observation_with_ofvs = Observation.from_json(j_observation_3_ofvs)
observation_field = ObservationField.from_json(j_obs_field_1)
ofv = ObservationFieldValue.from_json(j_ofv_1_numeric)
photo = Photo.from_json(j_photo_1)
photo_partial = Photo.from_json(j_photo_2_partial)
place = Place.from_json(j_place_1)
places_nearby = Place.from_json_list(j_places_nearby)
project = Project.from_json(j_project_1)
search_results = SearchResult.from_json_list(j_search_results)
taxon = Taxon.from_json(j_taxon_1)
taxon_partial = Taxon.from_json(j_taxon_2_partial)
taxon_counts = TaxonCounts.from_json(j_obs_species_counts)
taxon_summary = TaxonSummary.from_json(j_taxon_summary_2_listed)
user = User.from_json(j_user_1)

# Sample tables
tables = [
    format_table(observation_with_ofvs.annotations),
    format_table(observation.comments),
    format_table(ControlledTerm.from_json_list(j_controlled_terms)),
    format_table(observation.identifications),
    format_table(life_list),
    format_table([taxon_summary.listed_taxon, ListedTaxon.from_json(j_listed_taxon_2_partial)]),
    format_table([observation, observation_with_ofvs]),
    format_table(ObservationField.from_json_list(j_obs_fields)),
    format_table(observation_with_ofvs.ofvs),
    format_table([photo, photo_partial, observation.photos[0]]),
    format_table(places_nearby),
    format_table([project, project, project]),
    format_table(search_results),
    format_table(taxon_counts),
    format_table([taxon, observation_with_ofvs.taxon, observation.taxon]),
    format_table(User.from_json_list(j_users)),
]


if __name__ == '__main__':
    for table in tables:
        pprint(table)
    print(observation)
