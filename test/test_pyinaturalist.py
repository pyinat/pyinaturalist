"""
Tests for `pyinaturalist` module.
"""
import pytest
import requests_mock

from pyinaturalist.rest_api import get_access_token, AuthenticationError


class TestPyinaturalist(object):

    @classmethod
    def setup_class(cls):
        pass

    @requests_mock.Mocker(kw='mock')
    def test_get_access_token_fail(self, **kwargs):
        """ If we provide incorrect credentials to get_access_token(), an AuthenticationError is raised"""

        mock = kwargs['mock']
        rejection_json = {'error': 'invalid_client', 'error_description': 'Client authentication failed due to '
                                                                          'unknown client, no client authentication '
                                                                          'included, or unsupported authentication '
                                                                          'method.'}
        mock.post('https://www.inaturalist.org/oauth/token', json=rejection_json, status_code=401)

        with pytest.raises(AuthenticationError):
            get_access_token('username', 'password', 'app_id', 'app_secret')

    @requests_mock.Mocker(kw='mock')
    def test_get_access_token(self, **kwargs):
        """ Test a successful call to get_access_token() """

        mock = kwargs['mock']
        accepted_json = {'access_token': '604e5df329b98eecd22bb0a84f88b68a075a023ac437f2317b02f3a9ba414a08',
                         'token_type': 'Bearer', 'scope': 'write', 'created_at': 1539352135}
        mock.post('https://www.inaturalist.org/oauth/token', json=accepted_json, status_code=200)

        token = get_access_token('valid_username', 'valid_password', 'valid_app_id', 'valid_app_secret')

        assert token == '604e5df329b98eecd22bb0a84f88b68a075a023ac437f2317b02f3a9ba414a08'

    @classmethod
    def teardown_class(cls):
        pass
