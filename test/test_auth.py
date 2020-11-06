import os
from unittest.mock import patch

import pytest
from keyring.errors import KeyringError
from requests import HTTPError

from pyinaturalist.auth import get_access_token, get_keyring_credentials, set_keyring_credentials
from pyinaturalist.constants import INAT_BASE_URL
from pyinaturalist.exceptions import AuthenticationError
from test.conftest import MOCK_CREDS_ENV, MOCK_CREDS_OAUTH, load_sample_data

token_accepted_json = load_sample_data("get_access_token.json")
token_rejected_json = load_sample_data("get_access_token_401.json")


# get_access_token
# --------------------


@patch.dict(os.environ, {}, clear=True)
def test_get_access_token(requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/oauth/token",
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token("valid_username", "valid_password", "valid_app_id", "valid_app_secret")
    assert token == "604e5df329b98eecd22bb0a84f88b68"


@patch.dict(os.environ, MOCK_CREDS_ENV)
@patch("pyinaturalist.auth.get_keyring_credentials")
def test_get_access_token__envars(mock_keyring_credentials, requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/oauth/token",
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token()
    assert token == "604e5df329b98eecd22bb0a84f88b68"
    mock_keyring_credentials.assert_not_called()


@patch.dict(
    os.environ,
    {
        "INAT_USERNAME": "valid_username",
        "INAT_PASSWORD": "valid_password",
    },
)
def test_get_access_token__mixed_args_and_envars(requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/oauth/token",
        json=token_accepted_json,
        status_code=200,
    )

    token = get_access_token(app_id="valid_app_id", app_secret="valid_app_secret")
    assert token == "604e5df329b98eecd22bb0a84f88b68"


@patch.dict(os.environ, {}, clear=True)
@patch("pyinaturalist.auth.get_keyring_credentials", return_value=MOCK_CREDS_OAUTH)
@patch("pyinaturalist.auth.post")
def test_get_access_token__keyring(mock_post, mock_keyring_credentials, requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/oauth/token",
        json=token_accepted_json,
        status_code=200,
    )

    get_access_token()
    submitted_json = mock_post.call_args[1]["json"]
    assert submitted_json == {"grant_type": "password", **MOCK_CREDS_OAUTH}
    mock_keyring_credentials.assert_called()


@patch.dict(os.environ, {}, clear=True)
@patch("pyinaturalist.auth.get_keyring_credentials")
def test_get_access_token__missing_creds(mock_keyring_credentials):
    with pytest.raises(AuthenticationError):
        get_access_token("username")


def test_get_access_token__invalid_creds(requests_mock):
    requests_mock.post(
        f"{INAT_BASE_URL}/oauth/token",
        json=token_rejected_json,
        status_code=401,
    )

    with pytest.raises(HTTPError):
        get_access_token("username", "password", "app_id", "app_secret")


# get_keyring_credentials
# -------------------------


@patch("keyring.get_password", side_effect=list(MOCK_CREDS_OAUTH.values()))
def test_get_keyring_credentials(get_password):
    assert get_keyring_credentials() == MOCK_CREDS_OAUTH


def test_get_keyring_credentials__not_installed():
    pass


@patch("keyring.get_password", side_effect=KeyringError)
def test_get_keyring_credentials__no_backend(get_password):
    assert get_keyring_credentials() == {}


# get_keyring_credentials
# -------------------------


@patch("keyring.set_password")
def test_set_keyring_credentials(set_password):
    set_keyring_credentials("username", "password", "app_id", "app_secret")
    assert set_password.call_count == 4
