from datetime import datetime

from pyinaturalist.constants import API_V1
from pyinaturalist.v1 import search
from test.conftest import load_sample_data


def test_search(requests_mock):
    """Simulate /search results with one of each record type"""
    requests_mock.get(
        f'{API_V1}/search',
        json=load_sample_data('get_search.json'),
        status_code=200,
    )
    response = search([8348, 6432])
    taxon_result = response['results'][0]
    place_result = response['results'][1]
    project_result = response['results'][2]
    user_result = response['results'][3]

    assert all([isinstance(result['score'], float) for result in response['results']])

    # Mainly just need to test type conversions
    assert taxon_result['type'] == 'Taxon'
    assert isinstance(taxon_result['record']['created_at'], datetime)

    assert place_result['type'] == 'Place'
    assert isinstance(place_result['record']['location'][0], float)
    assert isinstance(place_result['record']['location'][1], float)

    assert project_result['type'] == 'Project'
    assert isinstance(project_result['record']['last_post_at'], datetime)

    assert user_result['type'] == 'User'
    assert isinstance(user_result['record']['created_at'], datetime)
