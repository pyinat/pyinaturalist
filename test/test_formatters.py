# flake8: noqa: F405
import re
from io import StringIO

import pytest
from requests import Request
from requests_cache import CachedResponse
from rich.console import Console
from rich.table import Table

from pyinaturalist.constants import API_V0
from pyinaturalist.formatters import *
from test.sample_data import *

# Lists of JSON records that can be formatted into tables
TABULAR_RESPONSES = [
    j_comments,
    [j_annotation_1],
    [j_controlled_term_1, j_controlled_term_2],
    [j_identification_1, j_identification_2],
    [j_observation_1, j_observation_2],
    j_obs_species_counts,
    j_life_list,
    [j_listed_taxon_1, j_listed_taxon_2_partial],
    [j_message],
    [j_photo_1, j_photo_2_partial],
    [j_place_1, j_place_2],
    j_places_nearby,
    [j_project_1, j_project_2],
    j_search_results,
    [j_taxon_1, j_taxon_2_partial],
    [j_user_1, j_user_2_partial],
]


def get_variations(response_object):
    """Formatting functions should accept any of these variations"""
    return [{'results': [response_object]}, [response_object], response_object]


# TODO: More thorough tests for table content
@pytest.mark.parametrize('response', TABULAR_RESPONSES)
def test_format_table(response):
    table = format_table(response)
    assert isinstance(table, Table)

    def _get_id(value):
        return str(
            value.get('id')
            or value.get('record', {}).get('id')
            or value.get('taxon', {}).get('id')
            or value.get('controlled_attribute', {}).get('id')
        )

    # Just make sure at least object IDs show up in the table
    console = Console()
    rendered = '\n'.join([str(line) for line in console.render_lines(table)])

    if isinstance(response, list):
        assert all([_get_id(value) in rendered for value in response])

    # for obj in response:
    #     assert all([value in rendered_table for value in obj.row.values()])


def test_format_table__unknown_type():
    with pytest.raises(ValueError):
        format_table({'foo': 'bar'})


# TODO: Test content written to stdout. For now, just make sure it doesn't explode.
@pytest.mark.parametrize('response', TABULAR_RESPONSES)
def test_pprint(response):
    console = Console(force_terminal=False, width=120)
    with console.capture() as output:
        pprint(response)
    rendered = output.get()


PRINTED_OBSERVATION = """
Observation(
    id=16227955,
    created_at='2018-09-05 14:31:08+02:00',
    captive=False,
    community_taxon_id=493595,
    description='',
    identifications_count=2,
    identifications_most_agree=True,
    identifications_most_disagree=False,
    identifications_some_agree=True,
    license_code='CC0',
    location=(50.646894, 4.360086),
    mappable=True,
    num_identification_agreements=2,
    num_identification_disagreements=0,
    obscured=False,
    observed_on='2018-09-05 14:06:00+02:00',
    outlinks=[{'source': 'GBIF', 'url': 'http://www.gbif.org/occurrence/1914197587'}],
    owners_identification_from_vision=True,
    place_guess='54 rue des Badauds',
    place_ids=[7008, 8657, 14999, 59614, 67952, 80627, 81490, 96372, 96794, 97391, 97582, 108692],
    positional_accuracy=23,
    preferences={'prefers_community_taxon': None},
    public_positional_accuracy=23,
    quality_grade='research',
    reviewed_by=[180811, 886482, 1226913],
    site_id=1,
    species_guess='Lixus bardanae',
    updated_at='2018-09-22 19:19:27+02:00',
    uri='https://www.inaturalist.org/observations/16227955',
    uuid='6448d03a-7f9a-4099-86aa-ca09a7740b00',
    annotations=[],
    comments=[
        Comment(id=2071896, username='borisb', created_at='Sep 05, 2018', truncated_body='I now see: Bonus species on observation! You ma...'),
        Comment(id=2071611, username='borisb', created_at='Sep 05, 2018', truncated_body='suspect L. bardanae - but sits on Solanum (non-...')
    ],
    identifications=[
        Identification(id=34896306, username='niconoe', taxon_name='Genus: Lixus', created_at='Sep 05, 2018', truncated_body=''),
        Identification(id=34926789, username='borisb', taxon_name='Species: Lixus bardanae', created_at='Sep 05, 2018', truncated_body=''),
        Identification(id=36039221, username='jpreudhomme', taxon_name='Species: Lixus bardanae', created_at='Sep 22, 2018', truncated_body='')
    ],
    ofvs=[],
    photos=[
        Photo(id=24355315, license_code='CC-BY', url='https://static.inaturalist.org/photos/24355315/square.jpeg?1536150664'),
        Photo(id=24355313, license_code='CC-BY', url='https://static.inaturalist.org/photos/24355313/square.jpeg?1536150659')
    ],
    project_observations=[],
    taxon=Taxon(id=493595, full_name='Species: Lixus bardanae'),
    user=User(id=886482, login='niconoe', name='Nicolas Noé')
)
"""


def test_pretty_print():
    """Test rich.pretty with modifications, via get_model_fields()"""
    console = Console(force_terminal=False, width=220, file=StringIO())
    observation = Observation.from_json(j_observation_1)

    console.print(observation)
    rendered = console.file.getvalue()
    print(rendered)

    # Don't check for differences in indendtation
    rendered = re.sub(' +', ' ', rendered.strip())
    expected = re.sub(' +', ' ', PRINTED_OBSERVATION.strip())

    # Emoji may not correctly render in CI
    rendered = rendered.replace(r'\U0001fab2', '🪲')
    assert rendered == expected


def test_format_request():
    request = Request(
        method='GET',
        url=API_V0,
        headers={'Accept': 'application/json', 'Authorization': 'password123'},
        json={'client_secret': 'password123'},
    ).prepare()
    request_str = format_request(request)
    assert API_V0 in request_str
    assert 'Accept: application/json' in request_str
    assert 'password123' not in request_str


def test_format_response():
    response = CachedResponse(status_code=200, expires=datetime(2021, 1, 1), headers={'Age': '0'})
    response_str = format_response(response)

    assert 'cached; expires in ' in response_str
    assert 'Age: 0' in response_str
    response.expires = None
    assert 'never expires' in format_response(response)
