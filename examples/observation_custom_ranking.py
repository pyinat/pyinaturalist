#!/usr/bin/env python
# flake8: noqa: E241
"""Example of sorting an observation query using a custom ranking method.
This could, for example, help an identifier prioritize observations that are more likely to be
high-quality ones.

Extra requirements:
    pip install pandas requests_cache
"""
import json
from logging import basicConfig, getLogger
from os.path import dirname, isfile, join
from time import sleep

import pandas as pd
import requests_cache
from rich.progress import track

from pyinaturalist.node_api import get_identifications, get_observations
from pyinaturalist.request_params import ICONIC_TAXA, RANKS
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
    # 'account_age_days':                   0.5,   # Age of user account, in days
}

DATA_DIR = join(dirname(__file__), '..', 'downloads')
CACHE_FILE = join(DATA_DIR, 'inat_requests.db')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
CSV_COMBINED_EXPORT = join(DATA_DIR, 'combined-observations.csv')
USER_STATS_FILE = join(DATA_DIR, f'user_stats_{ICONIC_TAXON.lower()}.json')

logger = getLogger(__name__)
basicConfig(level='INFO')
getLogger('pyrate_limiter').setLevel('WARNING')
requests_cache.install_cache(backend='sqlite', cache_name=CACHE_FILE)


def append_user_stats(df):
    """Fetch user stats and append to a dataframe of observation records"""
    user_info = get_all_user_stats(df['user.id'].unique())
    for key in user_info[0].keys():
        logger.info(f'Updating observations with {key}')
        df[key] = df['user.id'].apply(lambda x: user_info[x])
    return df


def get_all_user_stats(user_ids):
    """Get some additional information about observers"""
    iconic_taxa_lookup = {v.lower(): k for k, v in ICONIC_TAXA.items()}
    iconic_taxon_id = iconic_taxa_lookup[ICONIC_TAXON.lower()]
    user_ids = set(user_ids)
    user_info = {}

    # Load previously saved stats, if any
    if isfile(USER_STATS_FILE):
        with open(USER_STATS_FILE) as f:
            user_info = {int(k): v for k, v in json.load(f).items()}
        logger.info(f'{len(user_info)} partial results loaded')

    n_users_remaining = len(user_ids) - len(user_info)
    logger.info(f'Getting stats for {n_users_remaining} unique users')
    logger.warning(
        'Estimated time, with default API request throttling: '
        f'{n_users_remaining / 30 / 60:.2f} hours'
    )
    for user_id in track(user_ids):
        if user_id in user_info:
            continue

        try:
            user_info[user_id] = get_user_stats(user_id, iconic_taxon_id)
        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            logger.error(f'Aborting and saving partial results to {USER_STATS_FILE}')
            break

    with open(USER_STATS_FILE, 'w') as f:
        json.dump(user_info, f)

    return user_info


def get_user_stats(user_id, iconic_taxon_id):
    """Get info for an individual user"""
    logger.debug(f'Getting stats for user {user_id}')
    user_observations = get_observations(
        user_id=user_id,
        iconic_taxa=ICONIC_TAXON,
        quality_grade='research',
        count_only=True,
    )
    user_identifications = get_identifications(
        user_id=user_id,
        iconic_taxon_id=iconic_taxon_id,
        count_only=True,
    )
    # user_age = datetime.now() - parse_date(user_info['created_at']).replace(tzinfo=None)
    # account_age_days = max(user_age.days, 1)

    return {
        'iconic_taxon_rg_observations_count': user_observations['total_results'],
        'iconic_taxon_identifications_count': user_identifications['total_results'],
    }


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
    logger.info(f'Formatting {len(df)} observation records')
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
    df = df.drop(columns=drop_cols)

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


def main(source='export'):
    if source == 'api':
        response = get_observations(iconic_taxa=ICONIC_TAXON, quality_grade='needs_id', page='all')
        df = to_dataframe(response['results'])
    else:
        df = load_combined_export()

    df = append_user_stats(df)
    df = rank_observations(df)

    # Save full and minimal results
    df.to_json(join(DATA_DIR, 'ranked_observations.json'))
    minify_observations(df).to_json(join(DATA_DIR, 'minified_observations.json'))

    return df


# if __name__ == '__main__':
#     main()
