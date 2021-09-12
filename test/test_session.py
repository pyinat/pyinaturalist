from unittest.mock import MagicMock, patch

import pytest

from pyinaturalist.session import (
    CACHE_FILE,
    MOCK_RESPONSE,
    ClientSession,
    delete,
    get,
    post,
    put,
    request,
)


# Just test that the wrapper methods call requests.request with the appropriate HTTP method
@pytest.mark.parametrize(
    'http_func, http_method',
    [(delete, 'DELETE'), (get, 'GET'), (post, 'POST'), (put, 'PUT')],
)
@patch('pyinaturalist.session.Session.send')
def test_http_methods(mock_send, http_func, http_method):
    http_func('https://url', key='value', session=None)
    request_obj = mock_send.call_args[0][0]

    assert request_obj.method == http_method
    assert request_obj.url == 'https://url/?key=value'
    assert request_obj.body is None


@patch('pyinaturalist.session.Session.send')
def test_request_headers(mock_send):
    """Test that the request() wrapper passes along expected headers"""
    request('GET', 'https://url', access_token='token')
    request_obj = mock_send.call_args[0][0]
    assert request_obj.headers['Authorization'] == 'Bearer token'


@patch('pyinaturalist.session.ClientSession')
def test_request_session(mock_ClientSession):
    mock_session = MagicMock()
    request('GET', 'https://url', session=mock_session)
    mock_session.send.assert_called()
    mock_ClientSession.assert_not_called()


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
@patch('pyinaturalist.session.getenv')
@patch('pyinaturalist.session.Session.send')
def test_request_dry_run(
    mock_send,
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
    with patch('pyinaturalist.session.pyinaturalist') as settings:
        settings.DRY_RUN_ENABLED = enabled_const
        settings.DRY_RUN_WRITE_ONLY = write_only_const
        response = request(method, 'http://url')

    # Verify that the request was or wasn't mocked based on settings
    if expected_real_request:
        assert mock_send.call_count == 1
        assert response == mock_send()
    else:
        assert response == MOCK_RESPONSE
        assert mock_send.call_count == 0


@patch('pyinaturalist.session.Session.send')
def test_request_dry_run_kwarg(mock_request):
    response = request('GET', 'http://url', dry_run=True)
    assert response == MOCK_RESPONSE
    assert mock_request.call_count == 0


# In addition to the test cases above, ensure that the request/response isn't altered with dry-run disabled
def test_request_dry_run_disabled(requests_mock):
    real_response = {'results': ['response object']}
    requests_mock.get('http://url', json={'results': ['response object']}, status_code=200)

    assert request('GET', 'http://url').json() == real_response


def test_session__cache_file():
    session = ClientSession()
    assert session.cache.responses.db_path == CACHE_FILE


def test_session__custom_expiration():
    session = ClientSession(expire_after=3600)
    assert session.expire_after == 3600
    assert session.urls_expire_after is None


def test_session__custom_retry():
    session = ClientSession(per_second=5)
    per_second_rate = session.limiter._rates[0]
    assert per_second_rate.limit / per_second_rate.interval == 5
