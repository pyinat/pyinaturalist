from io import BytesIO
from time import sleep
from unittest.mock import patch

import pytest
import urllib3.util.retry
from requests import ConnectionError, Request, Session
from requests_cache import CacheMixin
from requests_ratelimiter import Duration, HostBucketFactory, Limiter, Rate, SQLiteBucket
from urllib3.exceptions import MaxRetryError

from pyinaturalist.constants import (
    CACHE_EXPIRATION,
    CONNECT_TIMEOUT,
    REQUEST_TIMEOUT,
    WRITE_TIMEOUT,
)
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

    # Expect a MaxRetryError after exhausting retries
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
    assert session.cache.responses.db_path == CACHE_FILE


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


def test_session__custom_rate():
    session = ClientSession(per_second=5)
    per_second_rate = session.limiter.bucket_factory.rates[0]
    assert per_second_rate.limit / per_second_rate.interval * Duration.SECOND == 5


@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
@patch('requests_ratelimiter.requests_ratelimiter.Limiter')
def test_send__defaults(mock_limiter, mock_requests_send, mock_format):
    session = ClientSession()
    request = Request(method='GET', url='http://test.com').prepare()
    session.send(request)
    mock_requests_send.assert_called_with(request, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))


@pytest.mark.parametrize(
    'method, expected_timeout',
    [
        ('GET', REQUEST_TIMEOUT),
        ('HEAD', REQUEST_TIMEOUT),
        ('DELETE', REQUEST_TIMEOUT),
        ('POST', WRITE_TIMEOUT),
        ('PUT', WRITE_TIMEOUT),
    ],
)
@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
@patch('requests_ratelimiter.requests_ratelimiter.Limiter')
def test_send__write_timeout(
    mock_limiter, mock_requests_send, mock_format, method, expected_timeout
):
    session = ClientSession()
    request = Request(method=method, url='http://test.com').prepare()
    session.send(request)
    mock_requests_send.assert_called_with(request, timeout=(5, expected_timeout))


@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
@patch('requests_ratelimiter.requests_ratelimiter.Limiter')
def test_send__override_session_timeout(mock_limiter, mock_requests_send, mock_format):
    session = ClientSession(timeout=33, write_timeout=66)

    # read timeout
    request = Request(method='GET', url='http://test.com').prepare()
    session.send(request)
    mock_requests_send.assert_called_with(request, timeout=(5, 33))

    # write timeout
    request = Request(method='POST', url='http://test.com').prepare()
    session.send(request)
    mock_requests_send.assert_called_with(request, timeout=(5, 66))


@patch('pyinaturalist.session.format_response')
@patch('requests.sessions.Session.send')
@patch('requests_ratelimiter.requests_ratelimiter.Limiter')
def test_send__override_request_timeout(mock_limiter, mock_requests_send, mock_format):
    session = ClientSession()
    request = Request(method='POST', url='http://test.com').prepare()
    session.send(request, timeout=10)
    mock_requests_send.assert_called_with(request, timeout=(5, 10))


@patch.object(urllib3.util.retry.time, 'sleep')
def test_send__write_timeout_retry_success(mock_sleep, requests_mock):
    write_timeout_error = ConnectionError(
        'Connection aborted.', TimeoutError('The write operation timed out')
    )
    requests_mock.post(
        'http://test.com',
        [
            {'exc': write_timeout_error},  # first attempt: write timeout
            {'json': {'results': []}, 'status_code': 200},  # second attempt: success
        ],
    )

    session = ClientSession(max_retries=3)
    response = session.request('POST', 'http://test.com', raise_for_status=False)
    assert response.status_code == 200
    assert response.json() == {'results': []}


@patch.object(urllib3.util.retry.time, 'sleep')
def test_send__write_timeout_retry_exhausted(mock_sleep, requests_mock):
    write_timeout_error = ConnectionError(
        'Connection aborted.', TimeoutError('The write operation timed out')
    )
    requests_mock.post('http://test.com', exc=write_timeout_error)

    retries = 3
    session = ClientSession(max_retries=retries)
    with pytest.raises(MaxRetryError):
        session.request('POST', 'http://test.com', raise_for_status=False)
    assert mock_sleep.call_count == retries - 1


@patch.object(urllib3.util.retry.time, 'sleep')
def test_send__non_write_connection_error_not_retried(mock_sleep, requests_mock):
    requests_mock.post('http://test.com', exc=ConnectionError('Connection refused'))

    session = ClientSession(max_retries=3)
    with pytest.raises(ConnectionError):
        session.request('POST', 'http://test.com', raise_for_status=False)
    assert mock_sleep.call_count == 0


@pytest.mark.enable_client_session  # For all other tests, caching is disabled. Re-enable that here.
@patch.object(CacheMixin, 'send')
def test_send__cache_settings(mock_cache_send):
    """Per-request cache settings should be passed along to requests-cache"""
    session = ClientSession()
    request = Request(method='GET', url='http://test.com').prepare()
    mock_cache_send.return_value = MockResponse(request)

    session.get('http://test.com', expire_after=360)
    assert mock_cache_send.call_args.kwargs.get('expire_after') == 360

    session.get('http://test.com', refresh=True)
    assert mock_cache_send.call_args.kwargs.get('refresh') is True

    session.get('http://test.com', force_refresh=True)
    assert mock_cache_send.call_args.kwargs.get('force_refresh') is True


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
@patch('pyinaturalist.session.format_response')
@patch.object(Session, 'send')
def test_filelock(mock_send, mock_format, tmp_path):
    str(tmp_path / 'test.lock')
    session = ClientSession(
        bucket_class=FileLockSQLiteBucket,
    )
    # Send a request to initialize ratelimiter bucket(s)
    request = Request(method='GET', url='http://example.com').prepare()
    session.send(request)

    for bucket in session.limiter.bucket_factory.buckets.values():
        assert isinstance(bucket, SQLiteBucket)
        assert bucket.use_limiter_lock is True


def test_get_refresh_params():
    session = ClientSession()
    session.refresh_limiter = Limiter(HostBucketFactory(rates=[Rate(1, Duration.SECOND * 2)]))
    assert session.get_refresh_params('test') == {'refresh': True}
    assert session.get_refresh_params('test2') == {'refresh': True}
    assert session.get_refresh_params('test') == {'refresh': True, 'v': 1}
    assert session.get_refresh_params('test') == {'refresh': True, 'v': 2}
    sleep(2)
    assert session.get_refresh_params('test') == {'refresh': True}
