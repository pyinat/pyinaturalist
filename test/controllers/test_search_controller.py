from datetime import datetime

from pyinaturalist.client import iNatClient
from pyinaturalist.constants import API_V1
from pyinaturalist.models import Place, Project, Taxon, User
from test.sample_data import SAMPLE_DATA


def test_search(requests_mock):
    """Simulate /search results with one of each record type"""
    requests_mock.get(
        f'{API_V1}/search',
        json=SAMPLE_DATA['get_search'],
        status_code=200,
    )

    results = iNatClient().search([8348, 6432])
    assert len(results) == 4
    assert all(isinstance(result.score, float) for result in results)

    taxon_result = results[0]
    place_result = results[1]
    project_result = results[2]
    user_result = results[3]

    # Test value conversions
    assert taxon_result.type == 'Taxon'
    assert isinstance(taxon_result.record, Taxon)
    assert isinstance(taxon_result.record.created_at, datetime)
    assert taxon_result.record_name == 'Order Odonata (Dragonflies And Damselflies)'

    assert place_result.type == 'Place'
    assert isinstance(place_result.record, Place)
    assert isinstance(place_result.record.location[0], float)
    assert isinstance(place_result.record.location[1], float)
    assert place_result.record_name == 'Odonates of Peninsular India and Sri Lanka'

    assert project_result.type == 'Project'
    assert isinstance(project_result.record, Project)
    assert isinstance(project_result.record.last_post_at, datetime)
    assert project_result.record_name == 'Ohio Dragonfly Survey  (Ohio Odonata Survey)'

    assert user_result.type == 'User'
    assert isinstance(user_result.record, User)
    assert isinstance(user_result.record.created_at, datetime)
    assert user_result.record_name == 'odonatanb'
