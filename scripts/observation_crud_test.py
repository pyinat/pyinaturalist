#!/usr/bin/env python
# flake8: noqa: F401
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
from os.path import join
from pprint import pprint

from pyinaturalist import (
    create_observation,
    delete_observation,
    enable_logging,
    get_access_token,
    get_observation,
    put_observation_field_values,
    update_observation,
    upload,
)
from pyinaturalist.constants import SAMPLE_DATA_DIR

SAMPLE_PHOTO = join(SAMPLE_DATA_DIR, 'obs_image.jpg')
SAMPLE_SOUND = join(SAMPLE_DATA_DIR, 'obs_sound.wav')
enable_logging()


def run_observation_crud_test():
    token = get_access_token()
    print('Received access token')

    test_obs_id = create_test_obs(token)
    update_test_obs(test_obs_id, token)
    delete_test_obs(test_obs_id, token)
    print('Test complete')


def create_test_obs(token):
    response = create_observation(
        taxon_id=54327,
        observed_on=datetime.now(),
        description=(
            'This is a test observation used for testing [pyinaturalist](https://github.com/niconoe/pyinaturalist), '
            'and will be deleted shortly.'
        ),
        positional_accuracy=50,
        geoprivacy='open',
        access_token=token,
        observation_fields={297: 1},
        photos=[SAMPLE_PHOTO, SAMPLE_PHOTO],
        sounds=[SAMPLE_SOUND, SAMPLE_SOUND],
    )
    test_obs_id = response['id']
    print(f'Created new observation: {test_obs_id}')

    obs = get_observation(test_obs_id)
    print('Fetched new observation:')
    pprint(obs, indent=2)
    return test_obs_id


def update_test_obs(test_obs_id, token):
    response = upload(
        test_obs_id,
        photos=SAMPLE_PHOTO,
        access_token=token,
    )
    photo_id = response.get('photo').get('id')
    assert photo_id
    print(f'Added photo to observation: {photo_id}')
    # pprint(response, indent=2)

    response = update_observation(
        test_obs_id,
        taxon_id=54327,
        geoprivacy='obscured',
        ignore_photos=True,
        access_token=token,
    )
    new_geoprivacy = response[0]['geoprivacy']
    assert new_geoprivacy == 'obscured'
    print('Updated observation')
    # pprint(response, indent=2)

    # response = put_observation_field_values(
    #     observation_id=test_obs_id,
    #     observation_field_id=297,
    #     value=2,
    #     access_token=token,
    # )
    # print('Added observation field value:')
    # pprint(response, indent=2)


def delete_test_obs(test_obs_id, token):
    response = delete_observation(test_obs_id, token)
    # Empty response is expected
    print('Deleted observation')


if __name__ == '__main__':
    run_observation_crud_test()
