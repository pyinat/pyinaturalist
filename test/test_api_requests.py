import pytest
from time import sleep
from unittest.mock import MagicMock, patch

from pyrate_limiter import Duration, Limiter, RequestRate

import pyinaturalist
from pyinaturalist.api_requests import MOCK_RESPONSE, delete, get, post, put, ratelimit, request


# Just test that the wrapper methods call requests.request with the appropriate HTTP method
@pytest.mark.parametrize(
    'http_func, http_method',
    [(delete, 'DELETE'), (get, 'GET'), (post, 'POST'), (put, 'PUT')],
)
@patch('pyinaturalist.api_requests.Session.request')
def test_http_methods(mock_request, http_func, http_method):
    http_func('https://url', key='value', session=None)
    mock_request.assert_called_with(
        http_method,
        'https://url',
        params={'key': 'value'},
        headers={'Accept': 'application/json', 'User-Agent': pyinaturalist.user_agent},
        json=None,
        timeout=5,
    )


# Test that the requests() wrapper passes along expected headers; just tests kwargs, not mock response
@pytest.mark.parametrize(
    'input_kwargs, expected_headers',
    [
        ({}, {'Accept': 'application/json', 'User-Agent': pyinaturalist.user_agent}),
        (
            {'user_agent': 'CustomUA'},
            {'Accept': 'application/json', 'User-Agent': 'CustomUA'},
        ),
        (
            {'access_token': 'token'},
            {
                'Accept': 'application/json',
                'User-Agent': pyinaturalist.user_agent,
                'Authorization': 'Bearer token',
            },
        ),
    ],
)
@patch('pyinaturalist.api_requests.Session.request')
def test_request_headers(mock_request, input_kwargs, expected_headers):
    request('GET', 'https://url', **input_kwargs)
    request_kwargs = mock_request.call_args[1]
    assert request_kwargs['headers'] == expected_headers


@patch('pyinaturalist.api_requests.get_session')
def test_request_session(mock_get_session):
    mock_session = MagicMock()
    request('GET', 'https://url', session=mock_session)
    mock_session.request.assert_called()
    mock_get_session.assert_not_called()


# Test relevant combinations of dry-run settings and HTTP methods
@pytest.mark.parametrize(
    'enabled_const, enabled_env, write_only_const, write_only_env, method, expected_real_request',
    [
        # DRY_RUN_ENABLED constant or envar should mock GETs, but not DRY_RUN_WRITE_ONLY
        (False, False, False, False, 'GET', True),
        (False, False, True, True, 'GET', True),
        (False, False, False, False, 'HEAD', True),
        (True, False, False, False, 'GET', False),
        (False, True, False, False, 'GET', False),
        # Either DRY_RUN_ENABLED or DRY_RUN_WRITE_ONLY should mock POST requests
        (False, False, False, False, 'POST', True),
        (True, False, False, False, 'POST', False),
        (False, True, False, False, 'POST', False),
        (False, False, True, False, 'POST', False),
        (False, False, False, True, 'POST', False),
        (False, False, True, False, 'POST', False),
        # Same for the other write methods
        (False, False, False, False, 'PUT', True),
        (False, False, False, False, 'DELETE', True),
        (False, False, False, True, 'PUT', False),
        (False, False, False, True, 'DELETE', False),
        # Truthy environment variable strings should be respected
        (False, 'true', False, False, 'GET', False),
        (False, 'True', False, 'False', 'PUT', False),
        (False, False, False, 'True', 'DELETE', False),
        # As well as 'falsy' environment variable strings
        (False, 'false', False, False, 'GET', True),
        (False, 'none', False, 'False', 'POST', True),
        (False, False, False, 'None', 'DELETE', True),
    ],
)
@patch('pyinaturalist.api_requests.getenv')
@patch('pyinaturalist.api_requests.Session.request')
def test_request_dry_run(
    mock_request,
    mock_getenv,
    enabled_const,
    enabled_env,
    write_only_const,
    write_only_env,
    method,
    expected_real_request,
):
    # Mock any environment variables specified
    env_vars = {}
    if enabled_env is not None:
        env_vars['DRY_RUN_ENABLED'] = enabled_env
    if write_only_env is not None:
        env_vars['DRY_RUN_WRITE_ONLY'] = write_only_env
    mock_getenv.side_effect = env_vars.__getitem__

    # Mock constants and run request
    with patch('pyinaturalist.api_requests.pyinaturalist') as settings:
        settings.DRY_RUN_ENABLED = enabled_const
        settings.DRY_RUN_WRITE_ONLY = write_only_const
        response = request(method, 'http://url')

    # Verify that the request was or wasn't mocked based on settings
    if expected_real_request:
        assert mock_request.call_count == 1
        assert response == mock_request()
    else:
        assert response == MOCK_RESPONSE
        assert mock_request.call_count == 0


@patch('pyinaturalist.api_requests.Session.request')
def test_request_dry_run_kwarg(mock_request):
    response = request('GET', 'http://url', dry_run=True)
    assert response == MOCK_RESPONSE
    assert mock_request.call_count == 0


# In addition to the test cases above, ensure that the request/response isn't altered with dry-run disabled
def test_request_dry_run_disabled(requests_mock):
    real_response = {'results': ['response object']}
    requests_mock.get('http://url', json={'results': ['response object']}, status_code=200)

    assert request('GET', 'http://url').json() == real_response


@patch('pyinaturalist.api_requests.RATE_LIMITER', Limiter(RequestRate(5, Duration.SECOND)))
@patch('pyrate_limiter.limit_context_decorator.sleep', side_effect=sleep)
def test_ratelimit(mock_sleep):
    mock_func = MagicMock()

    for i in range(6):
        with ratelimit(bucket='pytest-1'):
            mock_func()

    # With 6 requests and a limit of 5 request/second, there should be a delay for the final request
    assert mock_func.call_count == 6
    assert mock_sleep.call_count == 1


@patch('pyinaturalist.api_requests.RATE_LIMITER', None)
@patch('pyrate_limiter.limit_context_decorator.sleep')
def test_ratelimit__no_limiter(mock_sleep):
    for i in range(70):
        with ratelimit():
            pass

    assert mock_sleep.call_count == 0
