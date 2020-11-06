import os
import pytest
from datetime import date, datetime
from dateutil.tz import gettz
from io import BytesIO
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from pyinaturalist.request_params import (
    preprocess_request_params,
    convert_bool_params,
    convert_datetime_params,
    convert_list_params,
    convert_observation_fields,
    ensure_file_obj,
    strip_empty_params,
    validate_ids,
    validate_multiple_choice_param,
    validate_multiple_choice_params,
)
import pyinaturalist.rest_api
import pyinaturalist.node_api
from test.conftest import MOCK_CREDS_ENV, get_module_http_functions, get_mock_args_for_signature

TEST_PARAMS = {
    "is_active": False,
    "only_id": "true",
    "preferred_place_id": [1, 2],
    "rank": ["phylum", "class"],
    "q": "",
    "locale": None,
    "parent_id": 1,
    "observation_fields": {1: "value"},
}


def test_convert_bool_params():
    params = convert_bool_params(TEST_PARAMS)
    assert params["is_active"] == "false"
    assert params["only_id"] == "true"


# Test some recognized date(time) formats, with and without TZ info, in date and non-date params
@pytest.mark.parametrize(
    "param, value, expected",
    [
        ("created_d1", "19951231T235959", "1995-12-31T23:59:59-08:00"),
        ("created_d2", "2008-08-08 08:08:08Z", "2008-08-08T08:08:08+00:00"),
        ("created_on", "2010-10-10 10:10:10-05:00", "2010-10-10T10:10:10-05:00"),
        ("created_on", "Jan 1 2000", "2000-01-01T00:00:00-08:00"),
        ("d1", "19970716", "1997-07-16T00:00:00-07:00"),
        ("q", date(1954, 2, 5), "1954-02-05"),
        ("q", datetime(1954, 2, 5), "1954-02-05T00:00:00-08:00"),
        ("q", "not a datetime", "not a datetime"),
    ],
)
@patch("pyinaturalist.request_params.tzlocal", return_value=gettz("US/Pacific"))
def test_convert_datetime_params(tzlocal, param, value, expected):
    converted = convert_datetime_params({param: value})
    assert converted[param] == expected


# Test both int and string lists
def test_convert_list_params():
    params = convert_list_params(TEST_PARAMS)
    assert params["preferred_place_id"] == "1,2"
    assert params["rank"] == "phylum,class"


def test_convert_observation_fields():
    params = convert_observation_fields(TEST_PARAMS)
    assert params["observation_field_values_attributes"] == [
        {"observation_field_id": 1, "value": "value"}
    ]


def test_ensure_file_obj__file_path():
    with NamedTemporaryFile() as temp:
        temp.write(b"test content")
        temp.seek(0)

        file_obj = ensure_file_obj(temp.name)
        assert file_obj.read() == b"test content"


def test_ensure_file_obj__file_obj():
    file_obj = BytesIO(b"test content")
    assert ensure_file_obj(file_obj) == file_obj


def test_strip_empty_params():
    params = strip_empty_params(TEST_PARAMS)
    assert len(params) == 6
    assert "q" not in params and "locale" not in params
    assert "is_active" in params and "only_id" in params


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1", "1"),
        (1, "1"),
        ("1,2,3", "1,2,3"),
        ([1, 2, 3], "1,2,3"),
        ([1e5, 2e5], "100000,200000"),
    ],
)
def test_validate_ids(value, expected):
    assert validate_ids(value) == expected


@pytest.mark.parametrize("value", ["NaN", "", None, []])
def test_validate_ids__invalid(value):
    with pytest.raises(ValueError):
        validate_ids("not a number")


# This is just here so that tests will fail if one of the conversion steps is removed
@patch("pyinaturalist.request_params.convert_bool_params")
@patch("pyinaturalist.request_params.convert_datetime_params")
@patch("pyinaturalist.request_params.convert_list_params")
@patch("pyinaturalist.request_params.strip_empty_params")
def test_preprocess_request_params(mock_bool, mock_datetime, mock_list, mock_strip):
    preprocess_request_params({"id": 1})
    assert all([mock_bool.called, mock_datetime.called, mock_list.called, mock_strip.called])


# The following tests ensure that all API requests call preprocess_request_params() at some point
# Almost all logic except the request is mocked out so this can generically apply to all API functions
# Using parametrization here so that on failure, pytest will show the specific function that failed
@pytest.mark.parametrize(
    "http_function", get_module_http_functions(pyinaturalist.node_api).values()
)
@patch("pyinaturalist.request_params.translate_rank_range")
@patch("pyinaturalist.response_format.as_geojson_feature")
@patch("pyinaturalist.node_api.convert_location_to_float")
@patch("pyinaturalist.node_api._convert_all_locations_to_float")
@patch("pyinaturalist.api_requests.preprocess_request_params")
@patch("pyinaturalist.api_requests.requests.request")
def test_all_node_requests_use_param_conversion(
    request,
    preprocess_request_params,
    convert_all_locations_to_float,
    convert_location_to_float,
    as_geojson,
    translate_rank_range,
    http_function,
):
    request().json.return_value = {"total_results": 1, "results": [{}]}
    mock_args = get_mock_args_for_signature(http_function)
    http_function(*mock_args)
    assert preprocess_request_params.call_count == 1


@pytest.mark.parametrize(
    "http_function", get_module_http_functions(pyinaturalist.rest_api).values()
)
@patch.dict(os.environ, MOCK_CREDS_ENV)
@patch("pyinaturalist.rest_api.convert_lat_long_to_float")
@patch("pyinaturalist.rest_api.sleep")
@patch("pyinaturalist.api_requests.preprocess_request_params")
@patch("pyinaturalist.api_requests.requests.request")
def test_all_rest_requests_use_param_conversion(
    request, preprocess_request_params, sleep, convert_lat_long_to_float, http_function
):
    # Handle the one API response that returns a list instead of a dict
    if http_function == pyinaturalist.rest_api.get_all_observation_fields:
        request().json.return_value = []
    else:
        request().json.return_value = {
            "total_results": 1,
            "access_token": "",
            "results": [],
        }

    mock_args = get_mock_args_for_signature(http_function)
    http_function(*mock_args)
    assert preprocess_request_params.call_count == 1


def test_validate_multiple_choice_param():
    params = {
        "param1": "valid_str",
        "param2": "invalid_str",
    }
    choices = ["str1", "str2", "valid_str"]

    validate_multiple_choice_param(params, "param1", choices)
    assert True
    with pytest.raises(ValueError):
        validate_multiple_choice_param(params, "param2", choices)


@pytest.mark.parametrize(
    "params",
    [
        {"csi": "LC"},
        {"csi": ["EW", "EX"]},
        {"geoprivacy": "open"},
        {"iconic_taxa": "Animalia"},
        {"identifications": "most_agree"},
        {"license": "CC-BY-NC"},
        {"rank": "order"},
        {"quality_grade": "research"},
        {"search_on": "tags"},
        {"geoprivacy": ["open", "obscured"]},
        {"geoprivacy": "open", "iconic_taxa": "Animalia", "license": "CC-BY-NC"},
    ],
)
def test_validate_multiple_choice_params(params):
    # If valid, there is no return value, but an exception should not be raised
    validate_multiple_choice_params(params)
    # If invalid, an exception should be raised
    with pytest.raises(ValueError):
        validate_multiple_choice_params({k: "Invalid_value" for k in params})
    # A valid + invalid value should also raise an exception
    with pytest.raises(ValueError):
        validate_multiple_choice_params({k: [v, "Invalid_value"] for k, v in params.items()})
