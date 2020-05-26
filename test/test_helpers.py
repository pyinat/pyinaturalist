from pyinaturalist.helpers import (
    convert_bool_params,
    convert_list_params,
    strip_empty_params,
)


TEST_PARAMS = {
    "parent_id": 1,
    "rank": ["phylum", "class"],
    "is_active": False,
    "only_id": "true",
    "q": "",
    "locale": None,
    "preferred_place_id": [1, 2],
}


def test_convert_bool_params():
    params = convert_bool_params(TEST_PARAMS)
    assert params["is_active"] == "false"
    assert params["only_id"] == "true"


def test_convert_list_params():
    params = convert_list_params(TEST_PARAMS)
    assert params["preferred_place_id"] == "1,2"
    assert params["rank"] == "phylum,class"


def test_strip_empty_params():
    params = strip_empty_params(TEST_PARAMS)
    assert len(params) == 5
    assert "q" not in params and "locale" not in params
    assert "is_active" in params and "only_id" in params
