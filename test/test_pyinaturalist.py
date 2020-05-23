"""
Tests for `pyinaturalist` module.
"""
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import requests_mock
from requests import HTTPError
from urllib.parse import urlencode, urljoin

import pyinaturalist
from pyinaturalist.constants import INAT_NODE_API_BASE_URL
from pyinaturalist.node_api import (
    get_observation,
    get_taxa,
    get_taxa_by_id,
    get_taxa_autocomplete,
)
from pyinaturalist.rest_api import (
    get_access_token,
    get_all_observation_fields,
    get_observation_fields,
    update_observation,
    create_observations,
    put_observation_field_values,
    delete_observation,
)
from pyinaturalist.exceptions import AuthenticationError, ObservationNotFound


def _sample_data_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_data", filename)


def _load_sample_json(filename):
    with open(_sample_data_path(filename), encoding="utf-8") as fh:
        return json.load(fh)


PAGE_1_JSON_RESPONSE = _load_sample_json("get_observation_fields_page1.json")
PAGE_2_JSON_RESPONSE = _load_sample_json("get_observation_fields_page2.json")


class TestNodeApi(object):
    def test_get_observation(self, requests_mock):
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "observations?id=16227955"),
            json=_load_sample_json("get_observation.json"),
            status_code=200,
        )

        obs_data = get_observation(observation_id=16227955)
        assert obs_data["quality_grade"] == "research"
        assert obs_data["id"] == 16227955
        assert obs_data["user"]["login"] == "niconoe"
        assert len(obs_data["photos"]) == 2

    def test_get_non_existent_observation(self, requests_mock):
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "observations?id=99999999"),
            json=_load_sample_json("get_nonexistent_observation.json"),
            status_code=200,
        )
        with pytest.raises(ObservationNotFound):
            get_observation(observation_id=99999999)

    def test_get_taxa(self, requests_mock):
        params = urlencode({"q": "vespi", "rank": "genus,subgenus,species"})
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "taxa?" + params),
            json=_load_sample_json("get_taxa.json"),
            status_code=200,
        )

        response = get_taxa(q="vespi", rank=["genus", "subgenus", "species"])
        first_result = response["results"][0]

        assert len(response["results"]) == 30
        assert response["total_results"] == 35
        assert first_result["id"] == 70118
        assert first_result["name"] == "Nicrophorus vespilloides"
        assert first_result["rank"] == "species"
        assert first_result["is_active"] is True
        assert len(first_result["ancestor_ids"]) == 14

    CLASS_AND_HIGHER = ["class", "superclass", "subphylum", "phylum", "kingdom"]
    SPECIES_AND_LOWER = ["form", "variety", "subspecies", "hybrid", "species"]
    CLASS_THOUGH_PHYLUM = ["class", "superclass", "subphylum", "phylum"]

    @pytest.mark.parametrize(
        "params, expected_ranks",
        [
            ({"rank": "genus"}, "genus"),
            ({"min_rank": "class"}, CLASS_AND_HIGHER),
            ({"max_rank": "species"}, SPECIES_AND_LOWER),
            ({"min_rank": "class", "max_rank": "phylum"}, CLASS_THOUGH_PHYLUM),
            ({"max_rank": "species", "rank": "override_me"}, SPECIES_AND_LOWER),
        ],
    )
    @patch("pyinaturalist.node_api.make_inaturalist_api_get_call")
    def test_get_taxa_by_rank_range(
        self, mock_inaturalist_api_get_call, params, expected_ranks,
    ):
        # Make sure custom rank params result in the correct 'rank' param value
        get_taxa(**params)
        mock_inaturalist_api_get_call.assert_called_with(
            "taxa", {"rank": expected_ranks}, user_agent=None
        )

    def test_get_taxa_by_id(self, requests_mock):
        taxon_id = 70118
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "taxa/" + str(taxon_id)),
            json=_load_sample_json("get_taxa_by_id.json"),
            status_code=200,
        )

        response = get_taxa_by_id(taxon_id)
        result = response["results"][0]
        assert len(response["results"]) == 1
        assert result["id"] == taxon_id
        assert result["name"] == "Nicrophorus vespilloides"
        assert result["rank"] == "species"
        assert result["is_active"] is True
        assert len(result["ancestors"]) == 12

        with pytest.raises(ValueError):
            get_taxa_by_id([1, 2])

    def test_get_taxa_autocomplete(self, requests_mock):
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "taxa/autocomplete?q=vespi"),
            json=_load_sample_json("get_taxa_autocomplete.json"),
            status_code=200,
        )

        response = get_taxa_autocomplete(q="vespi")
        first_result = response["results"][0]

        assert len(response["results"]) == 10
        assert response["total_results"] == 44
        assert first_result["matched_term"] == "Vespidae"
        assert first_result["id"] == 52747
        assert first_result["name"] == "Vespidae"
        assert first_result["rank"] == "family"
        assert first_result["is_active"] is True
        assert len(first_result["ancestor_ids"]) == 11

    def test_get_taxa_autocomplete_minified(self, requests_mock):
        requests_mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "taxa/autocomplete?q=vespi"),
            json=_load_sample_json("get_taxa_autocomplete.json"),
            status_code=200,
        )

        expected_results = [
            "   52747:       Family Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)",
            "   84738:    Subfamily Vespinae (Hornets and Yellowjackets)",
            "  131878:      Species Nicrophorus vespillo (Vespillo Burying Beetle)",
            "  495392:      Species Vespidae st1",
            "   70118:      Species Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)",
            "   84737:        Genus Vespina",
            "  621584:      Species Vespicula cypho",
            "  621585:      Species Vespicula trachinoides",
            "  621586:      Species Vespicula zollingeri",
            "  299443:      Species Vespita woolleyi",
        ]

        response = get_taxa_autocomplete(q="vespi", minify=True)
        assert response["results"] == expected_results


class TestRestApi(object):
    @requests_mock.Mocker(kw="mock")
    def test_get_observation_fields(self, **kwargs):
        """ get_observation_fields() work as expected (basic use)"""
        mock = kwargs["mock"]

        mock.get(
            "https://www.inaturalist.org/observation_fields.json?q=sex&page=2",
            json=PAGE_2_JSON_RESPONSE,
            status_code=200,
        )

        obs_fields = get_observation_fields(search_query="sex", page=2)
        assert obs_fields == PAGE_2_JSON_RESPONSE

    @requests_mock.Mocker(kw="mock")
    def test_get_all_observation_fields(self, **kwargs):
        """get_all_observation_fields() is able to paginate, accepts a search query and return correct results"""
        mock = kwargs["mock"]

        mock.get(
            "https://www.inaturalist.org/observation_fields.json?q=sex&page=1",
            json=PAGE_1_JSON_RESPONSE,
            status_code=200,
        )

        mock.get(
            "https://www.inaturalist.org/observation_fields.json?q=sex&page=2",
            json=PAGE_2_JSON_RESPONSE,
            status_code=200,
        )

        page_3_json_response = []
        mock.get(
            "https://www.inaturalist.org/observation_fields.json?q=sex&page=3",
            json=page_3_json_response,
            status_code=200,
        )

        all_fields = get_all_observation_fields(search_query="sex")
        assert all_fields == PAGE_1_JSON_RESPONSE + PAGE_2_JSON_RESPONSE

    @requests_mock.Mocker(kw="mock")
    def test_get_all_observation_fields_noparam(self, **kwargs):
        """get_all_observation_fields() can also be called without a search query without errors"""

        mock = kwargs["mock"]
        mock.get(
            "https://www.inaturalist.org/observation_fields.json?page=1",
            json=[],
            status_code=200,
        )

        get_all_observation_fields()

    @requests_mock.Mocker(kw="mock")
    def test_get_access_token_fail(self, **kwargs):
        """ If we provide incorrect credentials to get_access_token(), an AuthenticationError is raised"""

        mock = kwargs["mock"]
        rejection_json = {
            "error": "invalid_client",
            "error_description": "Client authentication failed due to "
            "unknown client, no client authentication "
            "included, or unsupported authentication "
            "method.",
        }
        mock.post(
            "https://www.inaturalist.org/oauth/token",
            json=rejection_json,
            status_code=401,
        )

        with pytest.raises(AuthenticationError):
            get_access_token("username", "password", "app_id", "app_secret")

    @requests_mock.Mocker(kw="mock")
    def test_get_access_token(self, **kwargs):
        """ Test a successful call to get_access_token() """

        mock = kwargs["mock"]
        accepted_json = {
            "access_token": "604e5df329b98eecd22bb0a84f88b68a075a023ac437f2317b02f3a9ba414a08",
            "token_type": "Bearer",
            "scope": "write",
            "created_at": 1539352135,
        }
        mock.post(
            "https://www.inaturalist.org/oauth/token",
            json=accepted_json,
            status_code=200,
        )

        token = get_access_token(
            "valid_username", "valid_password", "valid_app_id", "valid_app_secret"
        )

        assert (
            token == "604e5df329b98eecd22bb0a84f88b68a075a023ac437f2317b02f3a9ba414a08"
        )

    @requests_mock.Mocker(kw="mock")
    def test_update_observation(self, **kwargs):
        mock = kwargs["mock"]
        mock.put(
            "https://www.inaturalist.org/observations/17932425.json",
            json=_load_sample_json("update_observation_result.json"),
            status_code=200,
        )

        p = {
            "ignore_photos": 1,
            "observation": {"description": "updated description v2 !"},
        }
        r = update_observation(
            observation_id=17932425, params=p, access_token="valid token"
        )

        # If all goes well we got a single element representing the updated observation, enclosed in a list.
        assert len(r) == 1
        assert r[0]["id"] == 17932425
        assert r[0]["description"] == "updated description v2 !"

    @requests_mock.Mocker(kw="mock")
    def test_update_nonexistent_observation(self, **kwargs):
        """When we try to update a non-existent observation, iNat returns an error 410 with "obs does not longer exists". """
        mock = kwargs["mock"]
        mock.put(
            "https://www.inaturalist.org/observations/999999999.json",
            json={"error": "Cette observation n’existe plus."},
            status_code=410,
        )

        p = {
            "ignore_photos": 1,
            "observation": {"description": "updated description v2 !"},
        }

        with pytest.raises(HTTPError) as excinfo:
            update_observation(
                observation_id=999999999, params=p, access_token="valid token"
            )
        assert excinfo.value.response.status_code == 410
        assert excinfo.value.response.json() == {
            "error": "Cette observation n’existe plus."
        }

    @requests_mock.Mocker(kw="mock")
    def test_update_observation_not_mine(self, **kwargs):
        """When we try to update the obs of another user, iNat returns an error 410 with "obs does not longer exists"."""
        mock = kwargs["mock"]
        mock.put(
            "https://www.inaturalist.org/observations/16227955.json",
            json={"error": "Cette observation n’existe plus."},
            status_code=410,
        )

        p = {
            "ignore_photos": 1,
            "observation": {"description": "updated description v2 !"},
        }

        with pytest.raises(HTTPError) as excinfo:
            update_observation(
                observation_id=16227955,
                params=p,
                access_token="valid token for another user",
            )
        assert excinfo.value.response.status_code == 410
        assert excinfo.value.response.json() == {
            "error": "Cette observation n’existe plus."
        }

    @requests_mock.Mocker(kw="mock")
    def test_create_observation(self, **kwargs):
        mock = kwargs["mock"]

        mock.post(
            "https://www.inaturalist.org/observations.json",
            json=_load_sample_json("create_observation_result.json"),
            status_code=200,
        )

        params = {
            "observation": {"species_guess": "Pieris rapae"},
        }

        r = create_observations(params=params, access_token="valid token")
        assert len(r) == 1  # We added a single one
        assert (
            r[0]["latitude"] is None
        )  # We have the field, but it's none since we didn't submitted anything
        assert r[0]["taxon_id"] == 55626  # Pieris Rapae @ iNaturalist

    @requests_mock.Mocker(kw="mock")
    def test_create_observation_fail(self, **kwargs):
        mock = kwargs["mock"]
        params = {
            "observation": {
                "species_guess": "Pieris rapae",
                # Some invalid data so the observation is rejected...
                "observed_on_string": (datetime.now() + timedelta(days=1)).isoformat(),
                "latitude": 200,
            }
        }

        mock.post(
            "https://www.inaturalist.org/observations.json",
            json=_load_sample_json("create_observation_fail.json"),
            status_code=422,
        )

        with pytest.raises(HTTPError) as excinfo:
            create_observations(params=params, access_token="valid token")
        assert excinfo.value.response.status_code == 422
        assert (
            "errors" in excinfo.value.response.json()
        )  # iNat also give details about the errors

    @requests_mock.Mocker(kw="mock")
    def test_put_observation_field_values(self, **kwargs):
        mock = kwargs["mock"]
        mock.put(
            "https://www.inaturalist.org/observation_field_values/31",
            json=_load_sample_json("put_observation_field_value_result.json"),
            status_code=200,
        )

        r = put_observation_field_values(
            observation_id=18166477,
            observation_field_id=31,  # Animal behavior
            value="fouraging",
            access_token="valid token",
        )

        assert r["id"] == 31
        assert r["observation_field_id"] == 31
        assert r["observation_id"] == 18166477
        assert r["value"] == "fouraging"

    def test_delete_observation(self):
        # Blocked because the expected behaviour is still unclear because of
        # https://github.com/inaturalist/inaturalist/issues/2252
        pass

    @requests_mock.Mocker(kw="mock")
    def test_delete_unexisting_observation(self, **kwargs):
        """ObservationNotFound is raised if the observation doesn't exists"""
        mock = kwargs["mock"]
        mock.delete(
            "https://www.inaturalist.org/observations/24774619.json", status_code=404
        )

        with pytest.raises(ObservationNotFound):
            delete_observation(observation_id=24774619, access_token="valid token")

    @requests_mock.Mocker(kw="mock")
    def test_user_agent(self, **kwargs):
        # TODO: test for all functions that access the inaturalist API?
        mock = kwargs["mock"]
        mock.get(
            urljoin(INAT_NODE_API_BASE_URL, "observations?id=16227955"),
            json=_load_sample_json("get_observation.json"),
            status_code=200,
        )
        accepted_json = {
            "access_token": "604e5df329b98eecd22bb0a84f88b68a075a023ac437f2317b02f3a9ba414a08",
            "token_type": "Bearer",
            "scope": "write",
            "created_at": 1539352135,
        }
        mock.post(
            "https://www.inaturalist.org/oauth/token",
            json=accepted_json,
            status_code=200,
        )

        default_ua = "Pyinaturalist/{v}".format(v=pyinaturalist.__version__)

        # By default, we have a 'Pyinaturalist' user agent:
        get_observation(observation_id=16227955)
        assert mock._adapter.last_request._request.headers["User-Agent"] == default_ua
        get_access_token(
            "valid_username", "valid_password", "valid_app_id", "valid_app_secret"
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == default_ua

        # But if the user sets a custom one, it is indeed used:
        get_observation(observation_id=16227955, user_agent="CustomUA")
        assert mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA"
        get_access_token(
            "valid_username",
            "valid_password",
            "valid_app_id",
            "valid_app_secret",
            user_agent="CustomUA",
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA"

        # We can also set it globally:
        pyinaturalist.user_agent = "GlobalUA"
        get_observation(observation_id=16227955)
        assert mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"
        get_access_token(
            "valid_username", "valid_password", "valid_app_id", "valid_app_secret"
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"

        # And it persists across requests:
        get_observation(observation_id=16227955)
        assert mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"
        get_access_token(
            "valid_username", "valid_password", "valid_app_id", "valid_app_secret"
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"

        # But if we have a global and local one, the local has priority
        get_observation(observation_id=16227955, user_agent="CustomUA 2")
        assert mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA 2"
        get_access_token(
            "valid_username",
            "valid_password",
            "valid_app_id",
            "valid_app_secret",
            user_agent="CustomUA 2",
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA 2"

        # We can reset the global settings to the default:
        pyinaturalist.user_agent = pyinaturalist.DEFAULT_USER_AGENT
        get_observation(observation_id=16227955)
        assert mock._adapter.last_request._request.headers["User-Agent"] == default_ua
        get_access_token(
            "valid_username", "valid_password", "valid_app_id", "valid_app_secret"
        )
        assert mock._adapter.last_request._request.headers["User-Agent"] == default_ua
