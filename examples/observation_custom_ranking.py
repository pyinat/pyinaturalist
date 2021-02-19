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

# fmt: off
# TODO: Normalize values before applying weights
ICONIC_TAXON = 'Arachnida'
RANKING_WEIGHTS = {
    'iconic_taxon_rg_observations_count': 1.5,   # Number of research-grade observations for ICONIC_TAXON
    'iconic_taxon_identifications_count': 2.0,   # Number of identifications for ICONIC_TAXON
    'observations_count':                 0.05,  # Total observations (all taxa)
    'identifications_count':              0.05,  # Total identifications (all taxa)
    'account_age_days':                   0.8,   # Age of user account, in days
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
        user_stats[user_id]['account_age_days'] = user_age.days
        sleep(1)

    # Append user stats to the observation records
    for obs in observations:
        obs['user'].update(user_stats[obs['user']['id']])
    return observations


def get_observation_rank(observation):
    return sum([observation['user'][key] * RANKING_WEIGHTS[key] for key in RANKING_WEIGHTS])


def main():
    response = get_observations(iconic_taxa=ICONIC_TAXON, quality_grade='needs_id', per_page=200)
    observations = append_user_stats(response['results'])
    observations = sorted(observations, key=get_observation_rank)
    return observations


if __name__ == '__main__':
    main()
