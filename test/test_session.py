from io import BytesIO
from time import sleep
from unittest.mock import patch

import pytest
import urllib3.util.retry
from requests import Request, Session
from requests_ratelimiter import Limiter, RequestRate
from urllib3.exceptions import MaxRetryError

from pyinaturalist.constants import CACHE_EXPIRATION, REQUEST_TIMEOUT
from pyinaturalist.session import (
    CACHE_FILE,
    ClientSession,
    FileLockSQLiteBucket,
    MockResponse,
    clear_cache,
    delete,
    get,
    get_local_session,
    post,
    put,
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
    ClientSession().request('GET', 'https://url', access_token='token')
    request_obj = mock_send.call_args[0][0]
    assert request_obj.headers['Authorization'] == 'Bearer token'


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
@patch.object(Session, 'send')
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
    response = ClientSession().request(method, 'http://example.com')

    # Verify that the request was or wasn't mocked based on settings
    if expected_real_request:
        assert mock_send.call_count == 1
        assert response == mock_send()
    else:
        assert response.reason == 'DRY_RUN'
        assert mock_send.call_count == 0

        json_content = response.json()
        assert len(json_content['results']) == json_content['total_results'] == 0
        assert response.json()['arbitrary_key'] == ''


@patch.object(Session, 'send')
def test_request_dry_run_kwarg(mock_request):
    response = ClientSession().request('GET', 'http://url', dry_run=True)
    assert response.reason == 'DRY_RUN'
    assert mock_request.call_count == 0


# In addition to the test cases above, ensure that the request/response isn't altered with dry-run disabled
def test_request_dry_run_disabled(requests_mock):
    real_response = {'results': ['response object']}
    requests_mock.get('http://url', json=real_response, status_code=200)

    assert ClientSession().request('GET', 'http://url').json() == real_response


@patch.object(urllib3.util.retry.time, 'sleep')
def test_request_validate_json__retry_failure(mock_sleep, requests_mock):
    requests_mock.get(
        'http://url/invalid_json',
        body=BytesIO(b'{"results": "invalid respo"'),
        headers={'Content-Type': 'application/json'},
        status_code=200,
    )

    # Expect a MaxRetryError after exhausing retries
    retries = 7
    session = ClientSession(max_retries=retries)
    with pytest.raises(MaxRetryError) as e:
        session.get('http://url/invalid_json')
        assert 'JSONDecodeError' in str(e.value)
    assert mock_sleep.call_count == retries - 1


def test_request_validate_json__retry_success(requests_mock):
    requests_mock.get(
        'http://url/maybe_valid_json',
        [
            {
                'body': BytesIO(b'{"results": "invalid respo"'),
                'headers': {'Content-Type': 'application/json'},
                'status_code': 200,
            },
            {
                'body': BytesIO(b'{"results": "valid response"}'),
                'headers': {'Content-Type': 'application/json'},
                'status_code': 200,
            },
        ],
    )

    # Expect valid JSON on the second attempt
    session = ClientSession(max_retries=7)
    response = session.get('http://url/maybe_valid_json', refresh=True)
    assert response.json() == {'results': 'valid response'}


def test_session__cache_file():
    session = ClientSession()
    assert str(session.cache.responses.db_path) == CACHE_FILE


def test_session__custom_expiration():
    session = ClientSession(
        cache_control=False,
        expire_after=3600,
        urls_expire_after={
            'custom-domain/*': 3600,
            'api.inaturalist.org/v*/taxa*': 3600,
        },
    )
    assert session.settings.cache_control is False
    assert session.settings.expire_after == 3600

    # User-provided URL patterns should be appended to the default patterns
    assert session.settings.urls_expire_after['custom-domain/*'] == 3600
    assert session.settings.urls_expire_after['api.inaturalist.org/v*/taxa*'] == 3600
    assert session.settings.urls_expire_after['*'] == CACHE_EXPIRATION['*']


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
    mock_requests_send.assert_called_with(request, timeout=(5, REQUEST_TIMEOUT))


@pytest.mark.enable_client_session  # For all other tests, caching is disabled. Re-enable that here.
@patch.object(Session, 'send')
def test_session__send__cache_settings(mock_send):
    session = ClientSession()
    with patch.object(session, 'send') as mock_cache_send:
        request = Request(method='GET', url='http://test.com').prepare()
        mock_send.return_value = MockResponse(request)

        session.send(request)
        mock_cache_send.assert_called_with(request)

        session.send(request, expire_after=60, refresh=True)
        mock_cache_send.assert_called_with(request, expire_after=60, refresh=True)


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


@pytest.mark.enable_client_session
@patch.object(Session, 'send')
def test_filelock(mock_send, tmp_path):
    lock_path = str(tmp_path / 'test.lock')
    session = ClientSession(
        bucket_class=FileLockSQLiteBucket,
        lock_path=lock_path,
    )
    # Send a request to initialize ratelimiter bucket(s)
    request = Request(method='GET', url='http://example.com').prepare()
    session.send(request)

    for bucket in session.limiter.bucket_group.values():
        assert isinstance(bucket, FileLockSQLiteBucket)
        assert bucket._lock.lock_file == lock_path


def test_get_refresh_params():
    session = ClientSession()
    session.refresh_limiter = Limiter(RequestRate(1, 2))
    assert session.get_refresh_params('test') == {'refresh': True}
    assert session.get_refresh_params('test2') == {'refresh': True}
    assert session.get_refresh_params('test') == {'refresh': True, 'v': 1}
    assert session.get_refresh_params('test') == {'refresh': True, 'v': 2}
    sleep(2)
    assert session.get_refresh_params('test') == {'refresh': True}
