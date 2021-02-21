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
from logging import basicConfig, getLogger
from time import sleep

import requests_cache

from pyinaturalist.node_api import get_identifications, get_observations
from pyinaturalist.response_format import to_dataframe

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

requests_cache.install_cache(backend='sqlite', cache_name='inat_requests.db')
logger = getLogger(__name__)
basicConfig(level='INFO')


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



def main():
    response = get_observations(iconic_taxa=ICONIC_TAXON, quality_grade='needs_id', per_page=200)
    observations = append_user_stats(response['results'])
    df = to_dataframe(observations)
    df = rank_observations(df)
    return observations


if __name__ == '__main__':
    main()
