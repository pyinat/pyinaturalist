import pytest
from unittest.mock import patch

import pyinaturalist
from pyinaturalist.api_requests import delete, get, post, put, request


# Just test that the wrapper methods call requests.request with the appropriate HTTP method
@pytest.mark.parametrize(
    "function, http_method",
    [(delete, "DELETE"), (get, "GET"), (post, "POST"), (put, "PUT")],
)
@patch("pyinaturalist.api_requests.request")
def test_http_methods(mock_request, function, http_method):
    function("https://url", param="value")
    mock_request.assert_called_with(http_method, "https://url", param="value")


# Test that the requests() wrapper passes along expected headers; just tests kwargs, not mock response
@pytest.mark.parametrize(
    "input_kwargs, expected_headers",
    [
        ({}, {"Accept": "application/json", "User-Agent": pyinaturalist.user_agent}),
        (
            {"user_agent": "CustomUA"},
            {"Accept": "application/json", "User-Agent": "CustomUA"},
        ),
        (
            {"access_token": "token"},
            {"Accept": "application/json", "User-Agent": pyinaturalist.user_agent, "Authorization": "Bearer token",},
        ),
    ],
)
@patch("pyinaturalist.api_requests.requests.request")
def test_request_headers(mock_request, input_kwargs, expected_headers):
    request("GET", "https://url", **input_kwargs)
    request_kwargs = mock_request.call_args[1]
    assert request_kwargs["headers"] == expected_headers
