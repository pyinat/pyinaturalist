import os
import pytest
from urllib.parse import urlencode, urljoin
from unittest.mock import patch

import pyinaturalist
from pyinaturalist.constants import INAT_NODE_API_BASE_URL, PER_PAGE_RESULTS
from pyinaturalist.node_api import (
    get_observation,
    get_observations,
    get_all_observations,
    get_observation_species_counts,
    get_all_observation_species_counts,
    get_geojson_observations,
    get_places_by_id,
    get_places_nearby,
    get_places_autocomplete,
    get_projects,
    get_projects_by_id,
    get_taxa,
    get_taxa_by_id,
    get_taxa_autocomplete,
)
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.rest_api import get_access_token
from test.conftest import load_sample_data


# Observations
# --------------------


def test_get_observation(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_observation.json"),
        status_code=200,
    )

    observation = get_observation(16227955)
    assert observation["quality_grade"] == "research"
    assert observation["id"] == 16227955
    assert observation["user"]["login"] == "niconoe"
    assert len(observation["photos"]) == 2


def test_get_observations(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_observations_node_page1.json"),
        status_code=200,
    )

    observations = get_observations(
        taxon_name="Danaus plexippus",
        created_on="2020-08-27",
        photos=True,
        geo=True,
        geoprivacy="open",
        place_id=7953,
    )
    first_result = observations["results"][0]

    assert observations["total_results"] == 2
    assert len(observations["results"]) == 1
    assert first_result["taxon_geoprivacy"] == "open"
    assert first_result["observed_on"] == "2020-08-27"
    assert first_result["taxon"]["id"] == 48662
    assert len(first_result["place_ids"]) == 13


@patch("pyinaturalist.node_api.sleep")
def test_get_all_observations(sleep, requests_mock):
    # Make response appear as though there are more pages
    page_1 = load_sample_data("get_observations_node_page1.json")
    page_1["total_results"] = PER_PAGE_RESULTS + 1
    page_2 = load_sample_data("get_observations_node_page2.json")

    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        [
            {"json": page_1, "status_code": 200},
            {"json": page_2, "status_code": 200},
        ],
    )

    observations = get_all_observations(id=[57754375, 57707611])

    assert type(observations) is list
    assert len(observations) == 2


def test_get_geojson_observations(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_observation.json"),
        status_code=200,
    )

    geojson = get_geojson_observations(id=16227955)
    feature = geojson["features"][0]
    assert feature["geometry"]["coordinates"] == [4.360086, 50.646894]
    assert feature["properties"]["id"] == 16227955
    assert feature["properties"]["taxon_id"] == 493595


def test_get_geojson_observations__custom_properties(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_observation.json"),
        status_code=200,
    )

    properties = ["taxon_name", "taxon_rank"]
    geojson = get_geojson_observations(id=16227955, properties=properties)
    feature = geojson["features"][0]
    assert feature["properties"]["taxon_name"] == "Lixus bardanae"
    assert feature["properties"]["taxon_rank"] == "species"
    assert "id" not in feature["properties"] and "taxon_id" not in feature["properties"]


def test_get_non_existent_observation(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_nonexistent_observation.json"),
        status_code=200,
    )
    with pytest.raises(ObservationNotFound):
        get_observation(99999999)


def test_get_observation_species_counts(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations/species_counts"),
        json=load_sample_data("get_observation_species_counts.json"),
        status_code=200,
    )
    response = get_observation_species_counts(user_login="my_username", quality_grade="research")
    first_result = response["results"][0]

    assert first_result["count"] == 31
    assert first_result["taxon"]["id"] == 48484
    assert first_result["taxon"]["name"] == "Harmonia axyridis"


def test_get_all_observation_species_counts(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations/species_counts"),
        [
            {
                "json": load_sample_data("get_all_observation_species_counts_page1.json"),
                "status_code": 200,
            },
            {
                "json": load_sample_data("get_all_observation_species_counts_page2.json"),
                "status_code": 200,
            },
        ],
    )
    response = get_all_observation_species_counts(
        user_login="my_username", quality_grade="research"
    )
    first_result = response[0]
    last_result = response[-1]

    assert first_result["count"] == 19
    assert first_result["taxon"]["id"] == 27805
    assert first_result["taxon"]["name"] == "Notophthalmus viridescens"
    assert last_result["count"] == 1
    assert last_result["taxon"]["id"] == 39556
    assert last_result["taxon"]["name"] == "Apalone spinifera"


def test_get_observation_species_counts__invalid_multiple_choice_params():
    with pytest.raises(ValueError):
        get_observation_species_counts(quality_grade="None", iconic_taxa="slime molds")


# Places
# --------------------


def test_get_places_by_id(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "places/93735,89191"),
        json=load_sample_data("get_places_by_id.json"),
        status_code=200,
    )

    response = get_places_by_id([93735, 89191])
    result = response["results"][0]

    assert response["total_results"] == len(response["results"]) == 2
    assert result["id"] == 93735
    assert result["name"] == "Springbok"
    assert result["bbox_area"] == 0.000993854049
    assert result["location"] == [-29.665119, 17.88583]
    assert len(result["ancestor_place_ids"]) == 4


@pytest.mark.parametrize("place_id", ["asdf", [None], [1, "not a number"]])
def test_get_places_by_id__invalid_inputs(place_id):
    with pytest.raises(ValueError):
        get_places_by_id(place_id)


def test_get_places_nearby(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "places/nearby"),
        json=load_sample_data("get_places_nearby.json"),
        status_code=200,
    )

    response = get_places_nearby(nelat=150.0, nelng=-50.0, swlat=-149.999, swlng=-49.999)
    result = response["results"]["standard"][0]

    assert response["total_results"] == 20
    assert len(response["results"]["standard"]) + len(response["results"]["community"]) == 20

    assert result["id"] == 97394
    assert result["admin_level"] == -1
    assert result["name"] == "North America"
    assert result["bbox_area"] == 28171.40875125
    assert result["location"] == [56.7732555574, -179.68825]
    assert result["ancestor_place_ids"] is None


def test_get_places_autocomplete(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "places/autocomplete"),
        json=load_sample_data("get_places_autocomplete.json"),
        status_code=200,
    )

    response = get_places_autocomplete("springbok")
    result = response["results"][0]

    assert response["total_results"] == len(response["results"]) == 1
    assert result["id"] == 93735
    assert result["name"] == "Springbok"
    assert result["bbox_area"] == 0.000993854049
    assert result["location"] == [-29.665119, 17.88583]
    assert len(result["ancestor_place_ids"]) == 4


# Projects
# --------------------


def test_get_projects(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "projects"),
        json=load_sample_data("get_projects.json"),
        status_code=200,
    )

    response = get_projects(q="invasive", lat=49.27, lng=-123.08, radius=400, order_by="distance")
    first_result = response["results"][0]

    assert response["total_results"] == len(response["results"]) == 5
    assert first_result["id"] == 8291
    assert first_result["title"] == "PNW Invasive Plant EDDR"
    assert first_result["is_umbrella"] is False
    assert len(first_result["user_ids"]) == 33


def test_get_projects_by_id(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "projects/8348,6432"),
        json=load_sample_data("get_projects_by_id.json"),
        status_code=200,
    )
    response = get_projects_by_id([8348, 6432])
    first_result = response["results"][0]

    assert response["total_results"] == len(response["results"]) == 2
    assert first_result["id"] == 8348
    assert first_result["title"] == "Tucson High Native and Invasive Species Inventory"
    assert first_result["place_id"] == 96103
    assert first_result["location"] == [32.2264416406, -110.9617278383]


# Taxa
# --------------------

CLASS_AND_HIGHER = ["class", "superclass", "subphylum", "phylum", "kingdom"]
SPECIES_AND_LOWER = ["form", "variety", "subspecies", "hybrid", "species"]
CLASS_THOUGH_PHYLUM = ["class", "superclass", "subphylum", "phylum"]


def test_get_taxa(requests_mock):
    params = urlencode({"q": "vespi", "rank": "genus,subgenus,species"})
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "taxa?" + params),
        json=load_sample_data("get_taxa.json"),
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
    mock_inaturalist_api_get_call,
    params,
    expected_ranks,
):
    # Make sure custom rank params result in the correct 'rank' param value
    get_taxa(**params)
    kwargs = mock_inaturalist_api_get_call.call_args[1]
    requested_rank = kwargs["params"]["rank"]
    assert requested_rank == expected_ranks


# This is just a spot test of a case in which boolean params should be converted
@patch("pyinaturalist.api_requests.requests.request")
def test_get_taxa_by_name_and_is_active(request):
    get_taxa(q="Lixus bardanae", is_active=False)
    request_kwargs = request.call_args[1]
    assert request_kwargs["params"] == {"q": "Lixus bardanae", "is_active": "false"}


def test_get_taxa_by_id(requests_mock):
    taxon_id = 70118
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "taxa/" + str(taxon_id)),
        json=load_sample_data("get_taxa_by_id.json"),
        status_code=200,
    )

    response = get_taxa_by_id(taxon_id)
    result = response["results"][0]
    assert response["total_results"] == len(response["results"]) == 1
    assert result["id"] == taxon_id
    assert result["name"] == "Nicrophorus vespilloides"
    assert result["rank"] == "species"
    assert result["is_active"] is True
    assert len(result["ancestors"]) == 12


@pytest.mark.parametrize("taxon_id", ["asdf", [None], [1, "not a number"]])
def test_get_taxa_by_id__invalid_inputs(taxon_id):
    with pytest.raises(ValueError):
        get_taxa_by_id(taxon_id)


def test_get_taxa_autocomplete(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "taxa/autocomplete"),
        json=load_sample_data("get_taxa_autocomplete.json"),
        status_code=200,
    )

    response = get_taxa_autocomplete(q="vespi")
    first_result = response["results"][0]

    assert len(response["results"]) == 10
    assert response["total_results"] == 47
    assert first_result["matched_term"] == "Vespidae"
    assert first_result["id"] == 52747
    assert first_result["name"] == "Vespidae"
    assert first_result["rank"] == "family"
    assert first_result["is_active"] is True
    assert len(first_result["ancestor_ids"]) == 11


# Test usage of format_taxon() with get_taxa_autocomplete()
def test_get_taxa_autocomplete_minified(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "taxa/autocomplete"),
        json=load_sample_data("get_taxa_autocomplete.json"),
        status_code=200,
    )

    expected_results = [
        "   52747:       Family Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)",
        "   84738:    Subfamily Vespinae (Hornets and Yellowjackets)",
        "  131878:      Species Nicrophorus vespillo (Vespillo Burying Beetle)",
        "  621585:      Species Vespicula trachinoides (Vespicula Waspfish)",
        "  495392:      Species Vespidae st1",
        "   70118:      Species Nicrophorus vespilloides (Lesser Vespillo Burying Beetle)",
        "   92786:        Genus Vespicula",
        "  646195:        Genus Vespiodes",
        "  621584:      Species Vespicula cypho",
        "  621586:      Species Vespicula zollingeri",
    ]

    response = get_taxa_autocomplete(q="vespi", minify=True)
    print(response["results"])
    assert response["results"] == expected_results


@patch.dict(os.environ, {"GITHUB_REF": "refs/heads/master"}, clear=True)
def test_user_agent(requests_mock):
    requests_mock.get(
        urljoin(INAT_NODE_API_BASE_URL, "observations"),
        json=load_sample_data("get_observation.json"),
        status_code=200,
    )
    default_ua = pyinaturalist.DEFAULT_USER_AGENT

    # By default, we have a 'Pyinaturalist' user agent:
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == default_ua

    # But if the user sets a custom one, it is indeed used:
    get_observation(16227955, user_agent="CustomUA")
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA"

    # We can also set it globally:
    pyinaturalist.user_agent = "GlobalUA"
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"

    # And it persists across requests:
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == "GlobalUA"

    # But if we have a global and local one, the local has priority
    get_observation(16227955, user_agent="CustomUA 2")
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == "CustomUA 2"

    # We can reset the global settings to the default:
    pyinaturalist.user_agent = pyinaturalist.DEFAULT_USER_AGENT
    get_observation(16227955)
    assert requests_mock._adapter.last_request._request.headers["User-Agent"] == default_ua
