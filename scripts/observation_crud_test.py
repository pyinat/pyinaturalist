#!/usr/bin/env python
# ruff: noqa: F401
"""A partially automated script for testing all observation CRUD endpoints,
in absence of integration tests.
iNat credentials must be provided via environment variables.
See :py:func:`.get_access_token` for details.

Usage example:
```
export INAT_USERNAME=''
export INAT_PASSWORD=''
export INAT_APP_ID=''
export INAT_APP_SECRET=''
python scripts/obs_crud_test.py
```
"""
from datetime import datetime
from logging import getLogger
from os.path import join

from pyinaturalist import enable_logging, iNatClient
from pyinaturalist.constants import SAMPLE_DATA_DIR

SAMPLE_PHOTO = join(SAMPLE_DATA_DIR, 'obs_image.jpg')
SAMPLE_SOUND = join(SAMPLE_DATA_DIR, 'obs_sound.wav')
logger = getLogger('pyinaturalist.scripts')
enable_logging()


def run_observation_crud_test():
    client = iNatClient()

    test_obs_id = create_test_obs(client)
    update_test_obs(client, test_obs_id)
    delete_test_obs(client, test_obs_id)
    logger.info('Test complete')


def create_test_obs(client: iNatClient):
    response = client.observations.create(
        taxon_id=54327,
        observed_on=datetime.now(),
        description=(
            'This is a test observation used for testing '
            '[pyinaturalist](https://github.com/pyinat/pyinaturalist), '
            'and will be deleted shortly.'
        ),
        positional_accuracy=50,
        geoprivacy='open',
        observation_fields={297: 1},
        photos=[SAMPLE_PHOTO, SAMPLE_PHOTO],
        sounds=[SAMPLE_SOUND, SAMPLE_SOUND],
    )
    test_obs_id = response.id
    logger.info(f'Created new observation: {test_obs_id}')

    obs = client.observations.search(id=test_obs_id)
    logger.info('Fetched new observation:')
    logger.info(obs)
    return test_obs_id


def update_test_obs(client, test_obs_id):
    response = client.observations.upload(test_obs_id, photos=SAMPLE_PHOTO)
    photo_id = response[0].id
    assert photo_id
    logger.info(f'Added photo to observation: {photo_id}')

    response = client.observations.update(
        test_obs_id,
        taxon_id=54327,
        geoprivacy='obscured',
        description='Updated description',
    )
    new_geoprivacy = response.geoprivacy
    assert new_geoprivacy == 'obscured'
    logger.info('Updated observation')

    # response = put_observation_field_values(
    #     observation_id=test_obs_id,
    #     observation_field_id=297,
    #     value=2,
    #     access_token=token,
    # )
    # logger.info('Added observation field value:')


def delete_test_obs(client: iNatClient, test_obs_id):
    client.observations.delete(test_obs_id)
    logger.info(f'Deleted observation {test_obs_id}')


if __name__ == '__main__':
    run_observation_crud_test()
