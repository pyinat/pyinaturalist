#!/usr/bin/env python
"""A semi-automated script used to test all observation CRUD endpoints. Must provide iNat
credentials via environment variables. See :py:func:`.get_access_token` for details.
Usage example:
```
export INAT_USERNAME=""
export INAT_PASSWORD=""
export INAT_APP_ID=""
export INAT_APP_SECRET=""
python test/manual_tests/obs_crud_test.py
```
"""
from datetime import datetime
from os import getenv
from os.path import join
from pprint import pprint

from pyinaturalist.rest_api import (
    add_photo_to_observation,
    create_observation,
    delete_observation,
    get_access_token,
    put_observation_field_values,
    update_observation,
)
from pyinaturalist.node_api import get_observation
from test.conftest import SAMPLE_DATA_DIR

SAMPLE_PHOTO = join(SAMPLE_DATA_DIR, "obs_image.jpg")


def run_observation_crud_test():
    token = get_access_token()
    print("Received access token")

    test_obs_id = create_test_obs(token)
    update_test_obs(test_obs_id, token)
    delete_test_obs(test_obs_id, token)
    print("Test complete")


def create_test_obs(token):
    response = create_observation(
        taxon_id=54327,
        observed_on_string=datetime.now().isoformat(),
        description="This is a test observation used by pyinaturalist, and will be deleted shortly.",
        tag_list="wasp, Belgium",
        latitude=50.647143,
        longitude=4.360216,
        positional_accuracy=50,
        geoprivacy="open",
        access_token=token,
        observation_fields={297: 1},
    )
    test_obs_id = response[0]["id"]
    print(f"Created new observation: {test_obs_id}")

    obs = get_observation(test_obs_id)
    print("Fetched new observation:")
    pprint(obs, indent=2)
    return test_obs_id


def update_test_obs(test_obs_id, token):
    response = add_photo_to_observation(
        test_obs_id,
        photo=SAMPLE_PHOTO,
        access_token=token,
    )
    photo_id = response.get("photo").get("id")
    assert photo_id
    print(f"Added photo to observation: {photo_id}")
    # pprint(response, indent=2)

    response = update_observation(
        test_obs_id,
        taxon_id=54327,
        geoprivacy="obscured",
        ignore_photos=True,
        access_token=token,
    )
    new_geoprivacy = response[0]["geoprivacy"]
    assert new_geoprivacy == "obscured"
    print("Updated observation")
    # pprint(response, indent=2)

    # response = put_observation_field_values(
    #     observation_id=test_obs_id,
    #     observation_field_id=297,
    #     value=2,
    #     access_token=token,
    # )
    # print("Added observation field value:")
    # pprint(response, indent=2)


def delete_test_obs(test_obs_id, token):
    response = delete_observation(test_obs_id, token)
    # Empty response is expected
    print("Deleted observation")
    pprint(response, indent=2)


if __name__ == "__main__":
    run_observation_crud_test()
