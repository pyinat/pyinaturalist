#!/usr/bin/env python
# flake8: noqa: E241
"""Example of sorting an observation query using a custom ranking method.
This could, for example, help an identifier prioritize observations that are more likely to be
high-quality ones.

Extra requirements:
    pip install pandas requests_cache
"""
from datetime import datetime
from dateutil.parser import parse as parse_date
from glob import glob
from logging import basicConfig, getLogger
from os.path import basename, dirname, expanduser, isfile, join
from time import sleep

import pandas as pd
import requests_cache

from pyinaturalist.node_api import get_identifications, get_observations
from pyinaturalist.request_params import RANKS
from pyinaturalist.response_format import try_datetime
from pyinaturalist.response_utils import load_exports, to_dataframe

ICONIC_TAXON = 'Arachnida'

# Note: all values are normalized before ranking weights are applied.
# fmt: off
RANKING_WEIGHTS = {
    'iconic_taxon_rg_observations_count': 1.5,   # Number of research-grade observations for ICONIC_TAXON
    'iconic_taxon_identifications_count': 2.0,   # Number of identifications for ICONIC_TAXON
    'observations_count':                 0.1,   # Total observations (all taxa)
    'identifications_count':              0.1,   # Total identifications (all taxa)
    'account_age_days':                   0.5,   # Age of user account, in days
}

DATA_DIR = join(dirname(__file__), '..', 'downloads')
CACHE_FILE = join(DATA_DIR, 'inat_requests.db')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
CSV_COMBINED_EXPORT = join(DATA_DIR, 'combined-observations.csv')

requests_cache.install_cache(backend='sqlite', cache_name=CACHE_FILE)
logger = getLogger(__name__)
basicConfig(level='INFO')


# TODO: Refactor this to take a list of user records, return stats; update observations in dataframe instead of here
def append_user_stats(observations):
    """For each observation, get some additional info about the observer"""
    user_stats = {obs['user']['id']: obs['user'] for obs in observations}

    # Only fetch stats once per user, since some users will have multiple observations
    logger.info(
        f'Getting stats for {len(user_stats)} unique observers of '
        f'{len(observations)} total observations'
    )
    logger.warning(f'Estimated time, with conservative API request throttling: {len(user_stats)/60} minutes')
    for user_id, user_info in user_stats.items():
        logger.debug(f'Getting stats for user {user_id}')
        user_obs = get_observations(
            user_id=user_id,
            iconic_taxa=ICONIC_TAXON,
            quality_grade='research',
            per_page=0,
        )
        user_ids = get_identifications(user_id=user_id, iconic_taxa=ICONIC_TAXON, per_page=0)
        user_age = datetime.now() - parse_date(user_info['created_at']).replace(tzinfo=None)

        user_stats[user_id]['iconic_taxon_rg_observations_count'] = user_obs['total_results']
        user_stats[user_id]['iconic_taxon_identifications_count'] = user_ids['total_results']
        user_stats[user_id]['account_age_days'] = max(user_age.days, 1)
        sleep(1)

    # Append user stats to the observation records
    for obs in observations:
        obs['user'].update(user_stats[obs['user']['id']])
    return observations


def rank_observations(df):
    """Combine normalized and weighted values into a single ranking value, and sort"""
    def normalize(series):
        return (series - series.mean()) / series.std()

    df['rank'] = sum([normalize(df[key]) * weight for key, weight in RANKING_WEIGHTS.items()])
    return df.sort_values('rank')


def load_combined_export():
    """Either load and format raw export files, or load previously processed export file, if it
    exists
    """
    if isfile(CSV_COMBINED_EXPORT):
        return pd.read_csv(CSV_COMBINED_EXPORT)

    df = load_exports(CSV_EXPORTS)
    df = format_export(df)
    df.to_csv(CSV_COMBINED_EXPORT)
    return df


def format_export(df):
    """Format an exported CSV file to be similar to API response format"""
    replace_strs = {
        'common_name': 'taxon.preferred_common_name',
        'taxon_': 'taxon.',
        'user_': 'user.',
        '_name': '',
    }
    drop_cols = [
        'observed_on_string',
        'positioning_method',
        'positioning_device',
        'scientific',
        'time_observed_at',
        'time_zone',
    ]

    # Convert datetimes
    df['observed_on'] = df['observed_on_string'].apply(lambda x: try_datetime(x) or x)
    df['created_at'] = df['created_at'].apply(lambda x: try_datetime(x) or x)
    df['updated_at'] = df['updated_at'].apply(lambda x: try_datetime(x) or x)

    # Rename and drop selected columns
    def rename_column(col):
        for str_1, str_2 in replace_strs.items():
            col = col.replace(str_1, str_2)
        return col

    df = df.rename(columns={col: rename_column(col) for col in sorted(df.columns)})
    df = df.drop(columns=['observed_on_string', 'time_observed_at', 'time_zone'])

    def get_min_rank(series):
        for rank in RANKS:
            if series.get(f'taxon.{rank}'):
                return rank
        return ''

    # Fill out taxon name and rank
    df['taxon.rank'] = df.apply(get_min_rank, axis=1)
    df['taxon.name'] = df.apply(lambda x: x.get(f"taxon.{x['taxon.rank']}"), axis=1)

    return df.fillna('')


def minify_observations(df):
    """Get minimal info for ranked and sorted observations"""
    def get_default_photo(photos):
        return photos[0]['url'].rsplit('/', 1)[0]

    df['taxon.rank'] = df['taxon.rank'].apply(lambda x: f'{x.title()}: ')
    df['taxon'] = df['taxon.rank'] + df['taxon.name']
    df['photo'] = df['photos'].apply(get_default_photo)
    return df[['id', 'taxon', 'photo']]


def main():
    # WIP: Option to get data from export tool instead of API
    # df = load_combined_export()

    response = get_observations(iconic_taxa=ICONIC_TAXON, quality_grade='needs_id', per_page=200)
    observations = append_user_stats(response['results'])
    df = to_dataframe(observations)
    df = rank_observations(df)

    # Save full and minimal results
    df.to_json('ranked_observations.json')
    minify_observations('minified_observations.json')

    return observations


if __name__ == '__main__':
    main()
