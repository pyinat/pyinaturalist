#!/usr/bin/env python
# flake8: noqa: E241
"""Example of sorting an observation query using a custom ranking method.
This could, for example, help an identifier prioritize observations that are more likely to be
high-quality ones.

Extra requirements:
    pip install pandas requests_cache
"""
import json
import re
from datetime import datetime, timedelta
from logging import basicConfig, getLogger
from os import makedirs
from os.path import expanduser, isfile, join
from time import sleep

import pandas as pd
import requests_cache
from rich.progress import track

from pyinaturalist.constants import THROTTLING_DELAY
from pyinaturalist.node_api import get_identifications, get_observations, get_user_by_id
from pyinaturalist.request_params import ICONIC_TAXA, RANKS
from pyinaturalist.response_format import try_datetime
from pyinaturalist.response_utils import load_exports, to_dataframe

ICONIC_TAXON = 'Arachnida'
THROTTLING_DELAY = 3

# Note: all values are normalized before ranking weights are applied.
# fmt: off
RANKING_WEIGHTS = {
    'iqa_technical':                      2.0,   # Image quality assessment score
    'iqa_aesthetic':                      1.0,   # Secondary image quality assessment score
    'iconic_taxon_rg_observations_count': 1.5,   # Number of research-grade observations for ICONIC_TAXON
    'iconic_taxon_identifications_count': 2.0,   # Number of identifications for ICONIC_TAXON
    'observations_count':                 0.1,   # Total observations (all taxa)
    'identifications_count':              0.1,   # Total identifications (all taxa)
}

DATA_DIR = join(expanduser('~'), 'Downloads')
CACHE_FILE = join(DATA_DIR, 'inat_requests.db')
CSV_EXPORTS = join(DATA_DIR, 'observations-*.csv')
CSV_COMBINED_EXPORT = join(DATA_DIR, 'combined-observations.csv')
IQA_REPORTS = [join(DATA_DIR, 'iqa_aesthetic.json'), join(DATA_DIR, 'iqa_technical.json')]
USER_STATS_FILE = join(DATA_DIR, f'user_stats_{ICONIC_TAXON.lower()}.json')

PHOTO_ID_PATTERN = re.compile(r'.*photos/(.*)/.*\.(\w+)')

logger = getLogger(__name__)
basicConfig(level='INFO')
getLogger('pyrate_limiter').setLevel('WARNING')
requests_cache.install_cache(backend='sqlite', cache_name=CACHE_FILE)


def append_user_stats(df):
    """Fetch user stats and append to a dataframe of observation records"""
    # Sort user IDs by number of observations (in the current dataset) per user
    sorted_user_ids = dict(df['user.id'].value_counts()).keys()
    user_info = get_all_user_stats(sorted_user_ids)

    first_result = list(user_info.values())[0]
    for key in first_result.keys():
        logger.info(f'Updating observations with user.{key}')
        df[f'user.{key}'] = df['user.id'].apply(lambda x: user_info.get(x, {}).get(key))
    return df


def get_all_user_stats(user_ids, user_records=None):
    """Get some additional information about observers"""
    iconic_taxa_lookup = {v.lower(): k for k, v in ICONIC_TAXA.items()}
    iconic_taxon_id = iconic_taxa_lookup[ICONIC_TAXON.lower()]
    user_ids = set(user_ids)
    user_info = {}
    user_records = user_records or {}

    # Load previously saved stats, if any
    if isfile(USER_STATS_FILE):
        with open(USER_STATS_FILE) as f:
            user_info = {int(k): v for k, v in json.load(f).items()}
        logger.info(f'{len(user_info)} partial results loaded')

    # Estimate how long this thing is gonna take
    n_users_remaining = len(user_ids) - len(user_info)
    secs_per_user = (2 if user_records else 3) * THROTTLING_DELAY
    est_time = n_users_remaining / (60 / secs_per_user) / 60
    logger.info(f'Getting stats for {n_users_remaining} unique users')
    logger.warning(f'Estimated time, with default API request throttling: {est_time:.2f} hours')

    # Fetch results, and save partial results if interrupted
    for user_id in track(user_ids):
        if user_id in user_info:
            continue

        try:
            user_info[user_id] = get_user_stats(user_id, iconic_taxon_id, user_records.get(user_id))
        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            logger.error(f'Aborting and saving partial results to {USER_STATS_FILE}')
            break

    with open(USER_STATS_FILE, 'w') as f:
        json.dump(user_info, f)

    return user_info


def get_user_stats(user_id, iconic_taxon_id, user=None):
    """Get info for an individual user"""
    logger.debug(f'Getting stats for user {user_id}')
    # Full user info will already be available if fetched from API, but not for CSV exports
    if not user:
        user = get_user_by_id(user_id)
        sleep(THROTTLING_DELAY)
    user.pop('id', None)

    user_observations = get_observations(
        user_id=user_id,
        iconic_taxa=ICONIC_TAXON,
        quality_grade='research',
        count_only=True,
    )
    sleep(THROTTLING_DELAY)
    user_identifications = get_identifications(
        user_id=user_id,
        iconic_taxon_id=iconic_taxon_id,
        count_only=True,
    )
    sleep(THROTTLING_DELAY)

    user['iconic_taxon_rg_observations_count'] = user_observations['total_results']
    user['iconic_taxon_identifications_count'] = user_identifications['total_results']
    return user


def get_photo_id(image_url):
    """Get a photo ID from its URL (for CSV exports, which only include a URL)"""
    match = re.match(PHOTO_ID_PATTERN, str(image_url))
    return match.group(1) if match else ''


def rank_observations(df):
    """Combine normalized and weighted values into a single ranking value, and sort"""
    def normalize(series):
        return (series - series.mean()) / series.std()

    df['rank'] = sum([normalize(df[key]) * weight for key, weight in RANKING_WEIGHTS.items()])
    return df.sort_values('rank')


def load_observations_from_query(iconic_taxon=ICONIC_TAXON, days=60, **request_params):
    """Query all recent unidentified observations for the given iconic taxon"""
    response = get_observations(
        iconic_taxa=iconic_taxon,
        quality_grade='needs_id',
        d1=datetime.now() - timedelta(days=days),
        page='all',
        **request_params
    )
    df = to_dataframe(response['results'])
    df['photo.url'] = df['photos'].apply(lambda x: x[0]['url'])
    df['photo.id'] = df['photos'].apply(lambda x: x[0]['id'])
    return df


def load_observations_from_export():
    """Either load and format raw export files, or load previously processed export file, if it
    exists
    """
    makedirs(DATA_DIR, exist_ok=True)
    if isfile(CSV_COMBINED_EXPORT):
        logger.info(f'Loading {CSV_COMBINED_EXPORT}')
        return pd.read_csv(CSV_COMBINED_EXPORT)

    logger.info(f'Loading {CSV_EXPORTS}')
    df = load_exports(CSV_EXPORTS)
    df = format_export(df)
    df.to_csv(CSV_COMBINED_EXPORT)
    return df


def format_export(df):
    """Format an exported CSV file to be similar to API response format"""
    logger.info(f'Formatting {len(df)} observation records')
    replace_strs = {
        'common_name': 'taxon.preferred_common_name',
        'image_url': 'photo.url',
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

    # Add some other missing columns
    df['photo.id'] = df['photo.url'].apply(get_photo_id)

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
        df = load_observations_from_query(ICONIC_TAXON)
    else:
        df = load_observations_from_export()

    df = append_user_stats(df)
    df = rank_observations(df)

    # Save full and minimal results
    df.to_csv(CSV_COMBINED_EXPORT)
    minify_observations(df).to_json(join(DATA_DIR, 'minified_observations.json'))

    return df


# if __name__ == '__main__':
#     main()
