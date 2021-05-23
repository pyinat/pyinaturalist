import os
from unittest.mock import patch

import pyinaturalist
from pyinaturalist.constants import API_V1_BASE_URL
from pyinaturalist.v1 import get_observation
from test.conftest import load_sample_data


@patch.dict(os.environ, {'GITHUB_REF': 'refs/heads/main'}, clear=True)
def test_user_agent(requests_mock):
    requests_mock.get(
        f'{API_V1_BASE_URL}/observations',
        json=load_sample_data('get_observation.json'),
        status_code=200,
    )
    default_ua = pyinaturalist.DEFAULT_USER_AGENT

    # By default, we have a 'Pyinaturalist' user agent:
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == default_ua

    # But if the user sets a custom one, it is indeed used:
    get_observation(16227955, user_agent='CustomUA')
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == 'CustomUA'

    # We can also set it globally:
    pyinaturalist.user_agent = 'GlobalUA'
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == 'GlobalUA'

    # And it persists across requests:
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == 'GlobalUA'

    # But if we have a global and local one, the local has priority
    get_observation(16227955, user_agent='CustomUA 2')
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == 'CustomUA 2'

    # We can reset the global settings to the default:
    pyinaturalist.user_agent = pyinaturalist.DEFAULT_USER_AGENT
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers['User-Agent'] == default_ua
