from unittest.mock import MagicMock, patch

import pytest
from requests import Request

from pyinaturalist.session import (
    CACHE_FILE,
    MOCK_RESPONSE,
    ClientSession,
    clear_cache,
    delete,
    get,
    get_local_session,
    post,
    put,
    request,
)


# Just test that the wrapper methods call requests.request with the appropriate HTTP method
@pytest.mark.parametrize(
    'http_func, http_method',
    [(delete, 'DELETE'), (get, 'GET'), (post, 'POST'), (put, 'PUT')],
)
@patch('pyinaturalist.session.format_response')
@patch('pyinaturalist.session.Session.send')
def test_http_methods(mock_send, mock_format, http_func, http_method):
    http_func('https://url', key='value', session=None)
    request_obj = mock_send.call_args[0][0]

    assert request_obj.method == http_method
    assert request_obj.url == 'https://url/?key=value'
    assert request_obj.body is None


@patch('pyinaturalist.session.format_response')
@patch('pyinaturalist.session.Session.send')
def test_request_headers(mock_send, mock_format):
    """Test that the request() wrapper passes along expected headers"""
    request('GET', 'https://url', access_token='token')
    request_obj = mock_send.call_args[0][0]
    assert request_obj.headers['Authorization'] == 'Bearer token'


@patch('pyinaturalist.session.format_response')
@patch('pyinaturalist.session.ClientSession')
def test_request_session(mock_ClientSession, mock_format):
    mock_session = MagicMock()
    request('GET', 'https://url', session=mock_session)
    mock_session.send.assert_called()
    mock_ClientSession.assert_not_called()


# Test relevant combinations of dry-run settings and HTTP methods
@pytest.mark.parametrize(
    'enabled_env, write_only_env, method, expected_real_request',
    [
        # DRY_RUN_ENABLED should mock GETs, but not DRY_RUN_WRITE_ONLY
        (False, False, 'GET', True),
        (False, True, 'GET', True),
        (False, False, 'HEAD', True),
        (True, False, 'GET', False),
        # Either DRY_RUN_ENABLED or DRY_RUN_WRITE_ONLY should mock POST requests
        (False, False, 'POST', True),
        (True, False, 'POST', False),
        (False, True, 'POST', False),
        # Same for the other write methods
        (False, False, 'PUT', True),
        (False, False, 'DELETE', True),
        (False, True, 'PUT', False),
        (False, True, 'DELETE', False),
        # True/False environment variable strings should be respected
        ('true', False, 'GET', False),
        ('True', 'False', 'PUT', False),
        (False, 'True', 'DELETE', False),
        ('false', False, 'GET', True),
        ('none', 'False', 'POST', True),
        (False, 'None', 'DELETE', True),
    ],
)
@patch('pyinaturalist.session.format_response')
@patch('pyinaturalist.session.getenv')
@patch('pyinaturalist.session.Session.send')
def test_request_dry_run(
    mock_send,
    mock_getenv,
    mock_format,
    enabled_env,
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
    assert str(session.cache.responses.db_path) == CACHE_FILE


def test_session__custom_expiration():
    session = ClientSession(expire_after=3600)
    assert session.settings.expire_after == 3600
    assert not session.settings.urls_expire_after


def test_session__custom_retry():
    session = ClientSession(per_second=5)
    per_second_rate = session.limiter._rates[0]
    assert per_second_rate.limit / per_second_rate.interval == 5


@patch('requests.sessions.Session.send')
@patch('requests_ratelimiter.requests_ratelimiter.Limiter')
def test_session__send(mock_limiter, mock_requests_send):
    session = ClientSession()
    request = Request(method='GET', url='http://test.com').prepare()
    session.send(request)
    mock_requests_send.assert_called_with(request, timeout=(5, 10))


@pytest.mark.enable_client_session  # For all other tests, caching is disabled. Re-enable that here.
@patch('requests_cache.session.CacheMixin.send')
def test_session__send__cache_settings(mock_cache_send):
    session = ClientSession()
    request = Request(method='GET', url='http://test.com').prepare()

    session.send(request)
    mock_cache_send.assert_called_with(request, expire_after=None, refresh=False, timeout=(5, 10))

    session.send(request, expire_after=60, refresh=True)
    mock_cache_send.assert_called_with(request, expire_after=60, refresh=True, timeout=(5, 10))


def test_get_local_session():
    session_1 = get_local_session()
    session_2 = get_local_session()
    assert session_1 is session_2
    assert isinstance(session_1, ClientSession)


@pytest.mark.enable_client_session
def test_clear_cache():
    session = get_local_session()
    with patch.object(session, 'cache', autospec=True) as mock_cache:
        clear_cache()
        mock_cache.clear.assert_called()
