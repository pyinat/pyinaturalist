"""A script for mapping US county FIPS codes to iNaturalist place IDs.
This is a bit complicated, since we only have a text search endpoint to work with for iNat places.
"""
import json
import logging
import re
from collections import Counter
from csv import DictReader
from itertools import groupby
from os.path import dirname, isfile, join
from time import sleep
from typing import Any, Dict, List, Optional, Tuple

from unidecode import unidecode

from pyinaturalist.node_api import get_places_autocomplete

DATA_DIR = join(
    dirname(__file__),
    '..',
    'examples',
    'sample_data',
)
FIPS_CODES_FILE = join(DATA_DIR, 'us_county_fips_codes.csv')
SEARCH_RESULTS_FILE = join(DATA_DIR, 'us_county_search.json')
OUTPUT_FILE = join(DATA_DIR, 'fips_to_inat_place_ids.json')

FIPSDict = Dict[int, Dict[str, Any]]
ResultsList = List[Dict[str, Any]]
ResponseDict = Dict[int, ResultsList]

logging.basicConfig(level='INFO')


def get_counties() -> FIPSDict:
    """Read county info from CSV file
    Source: https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697
    (Plus some manual adjustments for alternative spellings)
    """
    with open(FIPS_CODES_FILE) as f:
        counties = list(DictReader(f))
    return {int(k): list(group)[0] for k, group in groupby(counties, key=lambda x: int(x['fips_code']))}


def load_search_results() -> Optional[ResponseDict]:
    if not isfile(SEARCH_RESULTS_FILE):
        return None
    with open(SEARCH_RESULTS_FILE) as f:
        return {int(k): v for k, v in json.load(f).items()}


def search_counties(counties: FIPSDict, fips_codes: List[int] = None) -> ResponseDict:
    """Search iNat for matching counties"""
    responses: ResponseDict = {}
    fips_codes = fips_codes or list(counties.keys())

    for i, fips in enumerate(fips_codes):
        county = counties[fips]
        for search_str in get_display_names(county):
            # If we already found a match, we don't need to try additional search strings
            if responses.get(fips) and get_matching_result(responses[fips], county, fips):
                continue

            print(f'Searching for county: "{search_str}" [{i+1}/{len(fips_codes)}]')
            response = get_places_autocomplete(search_str, page='all')
            # Add or append to results
            if response.get('results', []):
                responses.setdefault(fips, [])
                responses[fips] += response['results']
                print(f'  Found {len(response["results"])} results')
            sleep(0.5)

    with open(SEARCH_RESULTS_FILE, 'w') as f:
        json.dump(responses, f)

    return responses


def match_responses(responses: ResponseDict, counties: FIPSDict) -> Tuple[Dict[int, int], ResponseDict]:
    """Split responses into matching results (FIPS code -> iNat place ID) and nonmatching
    results
    """
    matches = {k: get_matching_result(v, counties[k], k) for k, v in responses.items()}
    matching_ids = {k: v['id'] for k, v in matches.items() if v}
    unmatched = {k: responses[k] for k, v in matches.items() if not v}
    return matching_ids, unmatched


def get_matching_result(results: ResultsList, county: Dict, fips_code: int) -> Optional[Dict]:
    """Get a search result that looks like it matches the specified county"""
    for result in results or []:
        if is_match(result, county):
            return result
    return None


def is_match(result, county):
    expected_names = [normalize_name(name) for name in get_display_names(county)]
    return normalize_name(result['display_name']) in expected_names


def normalize_name(name: str) -> str:
    name = unidecode(name.lower().replace('usa', 'us'))
    return re.sub('[^a-zA-Z]+', '', name)


def get_display_names(county: Dict) -> Tuple:
    """Get display names/search strings for the given county
    (or equivalent administrative division)
    """
    admin_division = ' County'
    county_name = county['county_name']

    # Some adjustments for states/regions with different naming conventions
    if county['state_abbr'] == 'PR':
        return (
            f"{county['county_name']}, PR",
            f"{county['county_name']}, Puerto Rico",
            f"{county['county_name']}",
        )
    if county['state_abbr'] == 'AS':
        return (
            f"{county['county_name']}, AS",
            f"{county['county_name']}, American Samoa",
            f"{county['county_name']}",
        )
    if county['state_abbr'] == 'LA':
        admin_division = ' Parish'
    if county['state_abbr'] == 'VA':
        county_name = county_name.replace(' City', '')

    return (
        f"{county_name}{admin_division} {county['state_abbr']}, US",
        f"{county_name}{admin_division} US, {county['state_abbr']}",
        f"{county_name}, US, {county['state_abbr']}",
        f"{county_name}, {county['state_abbr']}, US",
        f"{county_name}, {county['state_abbr']}",
    )


def main():
    counties = get_counties()
    # responses = search_counties(counties)
    responses = load_search_results()
    matching_ids, unmatched = match_responses(responses, counties)

    with open('fips_to_inat_lookup.json', 'w') as f:
        json.dump(matching_ids, f)


# Debugging
# ---------


def search(search_str, fips=None, counties=None):
    results = get_places_autocomplete(search_str, page='all').get('results', [])
    if fips and counties:
        return summarize_results(results, fips, counties)
    else:
        return [r['display_name'] for r in results]


def summarize_results(results, fips, counties):
    county = counties[fips]
    return (
        get_display_names(county)[0] + '',
        [r['display_name'] for r in results],
        'Matches: ' + str(bool(get_matching_result(results, county, fips))),
    )


def summarize_responses(responses, counties):
    return {k: summarize_results(v, fips=k, counties=counties) for k, v in responses.items()}


def count_unmatched(unmatched, counties):
    return Counter([counties[fips]['state_abbr'] for fips in unmatched]).most_common()
