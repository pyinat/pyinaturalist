# pyinaturalist

[![Build status](https://github.com/niconoe/pyinaturalist/workflows/Build/badge.svg)](https://github.com/niconoe/pyinaturalist/actions)
[![Documentation Status (stable)](https://img.shields.io/readthedocs/pyinaturalist/stable?label=docs%20%28main%29)](https://pyinaturalist.readthedocs.io/en/stable/)
[![Documentation Status (latest)](https://img.shields.io/readthedocs/pyinaturalist/latest?label=docs%20%28dev%29)](https://pyinaturalist.readthedocs.io/en/latest/)
[![Coverage Status](https://coveralls.io/repos/github/niconoe/pyinaturalist/badge.svg?branch=main)](https://coveralls.io/github/niconoe/pyinaturalist?branch=main)
[![PyPI](https://img.shields.io/pypi/v/pyinaturalist?color=blue)](https://pypi.org/project/pyinaturalist)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/pyinaturalist)](https://pypi.org/project/pyinaturalist)
[![PyPI - Format](https://img.shields.io/pypi/format/pyinaturalist?color=blue)](https://pypi.org/project/pyinaturalist)

Pyinaturalist is an iNaturalist API client for python.
See full project documentation at https://pyinaturalist.readthedocs.io.

* [Summary](#pyinaturalist)
    + [Features](#features)
    + [Installation](#installation)
    + [Development Status](#development-status)
* [Usage Examples](#usage-examples)
    + [Observations](#observations)
    + [Species](#species)
* [Feedback](#feedback)

## Features

[iNaturalist](https://www.inaturalist.org) is a rich source of biodiversity data, and offers an
extensive API to interact with nearly every aspect of its platform.

If you want to make use of these data within a python application, script, or notebook, then
pyinaturalist can help. It adds a number of python-specific conveniences, including:

* **Requests:** Simplified usage with python types and data structures
* **Responses:** Type conversions to things you would expect in python
  (for example, timestamps to timezone-aware `datetime` objects)
* **Server-Friendly Usage:** Client-side rate-limiting that follows the
  [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
* **Typing:** Complete parameter definitions with type annotations, which significantly enhances
  usability within an IDE, Jupyter notebook, or any other environment with type checking & autocompletion
* **Messages:** Improved error handling, which means less time spent figuring out why an API call failed
* **Docs:** Thorough documentation with example requests and responses
* **Security:** Keyring integration for secure credential storage
* **Testing:** A dry-run mode to preview your requests before potentially modifying data

Many of the most relevant API endpoints are included:
* **Searching for:**
    * controlled terms
    * identifications
    * observations
    * observation fields
    * observation species counts
    * places
    * projects
    * species
* **Text search autocompletion for:**
    * places
    * species
* **Creating and updating:**
    * observations
    * observation fields
    * observation photos

See
[Endpoints](https://pyinaturalist.readthedocs.io/en/latest/endpoints.html)
for a complete list of endpoints wrapped by pyinaturalist, see
[General Usage](https://pyinaturalist.readthedocs.io/en/latest/general_usage.html)
for features common to all or most endpoints, and see
[Reference](https://pyinaturalist.readthedocs.io/en/latest/reference.html)
to skip straight to the API docs.

## Installation

Install the latest stable version with pip:
```bash
$ pip install pyinaturalist
```

Or, if you would like to use the latest development (pre-release) version:
```bash
$ pip install --pre pyinaturalist
```

To install with minimal dependencies (which disables some optional features):
```bash
$ pip install --no-deps pyinaturalist
$ pip install python-dateutil requests
```

See
[Contributing](https://pyinaturalist.readthedocs.io/en/latest/contributing.html)
for details on setup for local development.

## Development Status
Pyinaturalist is under active development. More endpoints and features will continue to be added as
they are needed or requested.

* See [History](https://github.com/niconoe/pyinaturalist/blob/dev/HISTORY.md) for details on past and current releases
* See [Issues](https://github.com/niconoe/pyinaturalist/issues) for planned & proposed features
* [Create an issue](https://github.com/niconoe/pyinaturalist/issues/new/choose) if there is an endpoint
  or feature you would like to have added
* **PRs are welcome!**

## Usage Examples
Following are usage examples for some of the most commonly used basic features.

Also see the **examples/** folder for some more detailed examples.

### Observations

#### Search observations
There are [numerous fields you can search on](https://pyinaturalist.readthedocs.io/en/latest/modules/pyinaturalist.node_api.html#pyinaturalist.node_api.get_observations).
An obvious search to start with would be getting all of your own observations:
```python
from pyinaturalist.node_api import get_all_observations
obs = get_all_observations(user_id='my_username')
```

#### Get an access token
For authenticated API calls (creating/updating/deleting data), you first need to obtain an access token.
This requires creating an [iNaturalist app](https://www.inaturalist.org/oauth/applications/new).
```python
from pyinaturalist.auth import get_access_token
token = get_access_token(
    username='my_username',
    password='my_password',
    app_id='my_app_id',
    app_secret='my_app_secret',
)
```
See
[Authentication](https://pyinaturalist.readthedocs.io/en/latest/general_usage.html#authentication)
for additional authentication options, including environment variables and keyring services.

#### Create a new observation
```python
from pyinaturalist.rest_api import create_observation
from datetime import datetime

response = create_observation(
    taxon_id=54327,  # Vespa Crabro
    observed_on_string=datetime.now().isoformat(),
    time_zone='Brussels',
    description='This is a free text comment for the observation',
    tag_list='wasp, Belgium',
    latitude=50.647143,
    longitude=4.360216,
    positional_accuracy=50, # meters,
    # sets vespawatch_id (an observation field whose ID is 9613) to the value '100'.
    observation_fields={9613: 100},
    access_token=token,
)
new_observation_id = response[0]['id']
```

#### Upload a picture for this observation
```python
from pyinaturalist.rest_api import add_photo_to_observation

add_photo_to_observation(
    new_observation_id,
    access_token=token,
    photo='/Users/nicolasnoe/vespa.jpg',
)
```

#### Update an existing observation
```python
from pyinaturalist.rest_api import update_observation

update_observation(
    17932425,
    access_token=token,
    description='updated description !',
)
```

#### Get a list of all (globally available) observation fields
```python
from pyinaturalist.rest_api import get_all_observation_fields
response = get_all_observation_fields(search_query="DNA")
```

#### Set an observation field on an existing observation
[Observation Fields](https://www.inaturalist.org/pages/extra_fields_nz) are a way to add extra information
to your observations. They are similar to tags, but with a typed value.
```python
from pyinaturalist.rest_api import get_observation_fields, put_observation_field_values

# First find an observation field by name, if the ID is unknown
response = get_observation_fields('vespawatch_id')
observation_field_id = response[0]['id']

put_observation_field_values(
    observation_id=7345179,
    observation_field_id=observation_field_id,
    value=250,
    access_token=token,
)
```

#### Get observation data in alternative formats
A [separate endpoint](https://pyinaturalist.readthedocs.io/en/latest/modules/pyinaturalist.rest_api.html#pyinaturalist.rest_api.get_observations)
can provide other data formats, including Darwin Core, KML, and CSV:
```python
from pyinaturalist.rest_api import get_observations
obs = get_observations(user_id='niconoe', response_format='dwc')
```

#### Get observation species counts
You can also get counts of observations by species. On the iNaturalist web UI,
this information can be found on the 'Species' tab of search results.
For example, to get the counts of all your own research-grade observations:
```python
from pyinaturalist.node_api import get_observation_species_counts
obs_counts = get_observation_species_counts(user_id='my_username', quality_grade='research')
```

### Species

#### Search species and other taxa
Let's say you partially remember either a genus or family name that started with **'vespi'**-something:

```python
>>> from pyinaturalist.node_api import get_taxa
>>>
>>> response = get_taxa(q="vespi", rank=["genus", "family"])
>>> print({taxon["id"]: taxon["name"] for taxon in response["results"]})
{52747: "Vespidae", 84737: "Vespina", 92786: "Vespicula", 646195: "Vespiodes", ...}
```

Oh, that's right, it was **'Vespidae'**! Now let's find all of its subfamilies using its taxon ID
from the results above:

```python
>>> response = get_taxa(parent_id=52747)
>>> print({taxon["id"]: taxon["name"] for taxon in response["results"]})
{343248: "Polistinae", 84738: "Vespinae", 119344: "Eumeninae", 121511: "Masarinae", ...}
```

#### Get a species by ID
Let's find out more about this 'Polistinae' genus. We could search for it by name or by ID,
but since we already know the ID from the previous search, let's use that:

```python
>>> from pyinaturalist.node_api import get_taxa_by_id
>>> response = get_taxa_by_id(343248)
```

There is a lot of info in there, but let's just get the basics for now:

```python
>>> basic_fields = ["preferred_common_name", "observations_count", "wikipedia_url", "wikipedia_summary"]
>>> print({f: response["results"][0][f] for f in basic_fields})
{
    "preferred_common_name": "Paper Wasps",
    "observations_count": 69728,
    "wikipedia_url": "http://en.wikipedia.org/wiki/Polistinae",
    "wikipedia_summary": "The Polistinae are eusocial wasps closely related to the more familiar yellow jackets...",
}
```

#### Taxon autocomplete
This is a text search-optimized endpoint that provides autocompletion in the Naturalist web UI:

![Taxon autocompletion in the iNaturalist web UI](docs/images/taxon_autocomplete.png)

This one is a bit more niche, but it provides a fast way to search the iNaturalist taxonomy
database. Here is an example that will run searches from console input:

```python
from pyinaturalist.node_api import get_taxa_autocomplete

while True:
    query = input("> ")
    response = get_taxa_autocomplete(q=query, minify=True)
    print("\n".join(response["results"]))
```

Example usage:

```
> opilio
527573:     Genus Opilio
47367:      Order Opiliones (Harvestmen)
84644:      Species Phalangium opilio (European Harvestman)
527419:     Subfamily Opilioninae
...
> coleo
372759:     Subclass Coleoidea (Coleoids)
47208:      Order Coleoptera (Beetles)
359229:     Species Coleotechnites florae (Coleotechnites Flower Moth)
53502:      Genus Brickellia (brickellbushes)
...
<Ctrl-C>
```

If you get unexpected matches, the search likely matched a synonym, either in the form of a
common name or an alternative classification. Check the `matched_term` property for more
info. For example:

```python
>>> first_result = get_taxa_autocomplete(q='zygoca')['results'][0]
>>> first_result["name"]
"Schlumbergera truncata"
>>> first_result["matched_term"]
"Zygocactus truncatus"  # An older synonym for Schlumbergera
```

### ...And much more!
Check out the [Reference](https://pyinaturalist.readthedocs.io/en/latest/reference.html) section to
see what else you can do with pyinaturalist.

## Feedback
If you have any problems, suggestions, or questions about pyinaturalist, please let us know!
Just [create an issue here](https://github.com/niconoe/pyinaturalist/issues/new/choose).

**Note:** pyinaturalist is not directly affiliated with iNaturalist.org or the
California Academy of Sciences. If you have non-python-specific questions about iNaturalist, the
[iNaturalist Community Forum](https://forum.inaturalist.org/) is the best place to start.
