# General Usage
This page summarizes how to use the main features of pyinaturalist.

## Installation
Installation instructions:

::::{tab-set}
:::{tab-item} Pip
Install the latest stable version with pip:
```
pip install pyinaturalist
```
:::
:::{tab-item} Conda
Or install from conda-forge, if you prefer:
```
conda install -c conda-forge pyinaturalist
```
:::
:::{tab-item} Pre-release
If you would like to use the latest development (pre-release) version:
```
pip install --pre pyinaturalist
```
:::
:::{tab-item} Local development
See {ref}`contributing` for details on setup for local development.
:::
::::

:::{dropdown} Python version compatibility
:icon: info

pyinaturalist currently requires **python 3.8+**. If you need to use an older version
of python, here are the last compatible versions of pyinaturalist:

* **python 2.7:** pyinaturalist 0.1
* **python 3.4:** pyinaturalist 0.10
* **python 3.5:** pyinaturalist 0.11
* **python 3.6:** pyinaturalist 0.16
* **python 3.7:** pyinaturalist 0.19
* **python 3.8:** supported, but expected to be dropped in v1.0
:::

## Imports
You can import all public functions and classes from the top-level `pyinaturalist` package:
```
>>> from pyinaturalist import Taxon, get_observations, pprint  # etc.
```

Or you can just import everything:
```
>>> from pyinaturalist import *
```

## Requests
Requests generally follow the same format as the [API](https://api.inaturalist.org/v1)
and [search URLs](https://forum.inaturalist.org/t/how-to-use-inaturalists-search-urls-wiki).

For example, if you wanted to search observations by user, these three requests are equivalent:

::::{tab-set}
:::{tab-item} search URL
```
https://www.inaturalist.org/observations?user_id=tiwane,jdmore
```
:::
:::{tab-item} API request
```
https://api.inaturalist.org/v1/observations?user_id=tiwane%2Cjdmore
```
:::
:::{tab-item} pyinaturalist search
```python
>>> get_observations(user_id=['tiwane', 'jdmore'])
```
:::
::::

Compared to search URLs and raw API requests, pyinaturalist provides some conveniences for making
requests easier:
* Python lists instead of comma-separated strings
* Python booleans instead of JS-style boolean strings or `1`/`0`
* Python file-like objects or file paths for photo and sound uploads
* Python {py:class}`~datetime.date` and {py:class}`~datetime.datetime` objects instead of date/time strings
* Simplified data formats for `POST` and `PUT` requests
* Simplified pagination
* Validation for multiple-choice parameters

And more, depending on the function.
See the {ref}`reference-docs` section for a complete list of functions available.

## Responses
API responses are returned as JSON, with some python type conversions applied (similar to the
request type conversions mentioned above). Example response data is shown in the documentation for
each request function, for example {py:func}`~pyinaturalist.v1.observations.get_observations`.

### API Data vs Web UI
Here is how some of those response fields correspond to observation details shown on
iNaturalist.org:
```{figure} ../images/inat-observation-page-annotated.png
```

And here is what that same observation looks like in JSON:
:::{dropdown} Observation response JSON
:icon: code-square
```{literalinclude} ../sample_data/get_observation_2.json
```
:::

### Previewing Responses
These responses can contain large amounts of response attributes, making it somewhat cumbersome if you
just want to quickly preview results (for example, in a Jupyter notebook). For that purpose, the
{py:func}`~pyinaturalist.formatters.pprint` function is available to format response data as a
condensed, color-highlighted table.

**Examples:**

::::{tab-set}
:::{tab-item} Observations
```
>>> from pyinaturalist import get_observations, pprint
>>> observations = get_observations(user_id='niconoe', per_page=5)
>>> pprint(observations)
ID         Taxon ID   Taxon                                                  Observed on    User      Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
82974075   61546      Species: Nemophora degeerella (Yellow-barred Longhorn) Jun 14, 2021   niconoe   1428 Braine-l'Alleud, Belgique
82827577   48201      Family: Scarabaeidae (Scarabs)                         Jun 13, 2021   niconoe   1428 Braine-l'Alleud, Belgique
82826778   48201      Family: Scarabaeidae (Scarabs)                         Jun 13, 2021   niconoe   1428 Braine-l'Alleud, Belgique
82696354   209660     Species: Chrysolina americana (Rosemary Beetle)        Jun 12, 2021   niconoe   1420 Braine-l'Alleud, Belgique
82696334   472617     Species: Tomocerus vulgaris                            Jun 07, 2021   niconoe   1428 Braine-l'Alleud, Belgique
```
:::
:::{tab-item} Places
```
>>> from pyinaturalist import get_places, pprint
>>> places = get_places_autocomplete('Vale')
>>> pprint(places)
 ID       Latitude    Longitude   Name                  Category   URL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
96877      49.5189     -2.5190   Vale                             https://www.inaturalist.org/places/96877
21951     -16.8960    -40.8349   Fronteira dos Vales              https://www.inaturalist.org/places/21951
23663      -6.3677    -41.8001   Valença do Piauí                 https://www.inaturalist.org/places/23663
24222     -27.2220    -53.6338   Pinheirinho do Vale              https://www.inaturalist.org/places/24222
24374     -29.8309    -52.1121   Vale Verde                       https://www.inaturalist.org/places/24374
24442     -10.3841    -62.0939   Vale do Paraíso                  https://www.inaturalist.org/places/24442
103902     44.7355     27.5412   Valea Ciorii                     https://www.inaturalist.org/places/103902
103905     44.7529     26.8481   Valea Macrisului                 https://www.inaturalist.org/places/103905
105015     44.6805     24.0224   Valea Mare                       https://www.inaturalist.org/places/105015
104268     46.7917     27.0905   Valea Ursului                    https://www.inaturalist.org/places/104268
```
:::
:::{tab-item} Places (with terminal colors)
```{figure} ../images/pprint_table.png
```
:::
::::

(data-models)=
## Models
Data models ({py:mod}`pyinaturalist.models`) are included for all API response types. These allow
working with typed python objects, which are generally easier to work with than raw JSON.
They provide:
* Complete type annotations and autocompletion
* Condensed print formats for easy previewing with {py:func}`~pyinaturalist.formatters.pprint` (ideal for exploring data in Jupyter)
* Almost no performance overhead (on the order of nanoseconds per object)

To use these models with the standard API query functions, you can load JSON results
with `<Model>.from_json()` (single object) or `<Model>.from_json_list()` (list of objects):
```py
>>> from pyinaturalist import Observation, get_observations
>>> response = get_observations(user_id='my_username)
>>> observations = Observation.from_json_list(response)
```

And they can be converted back to a JSON dict if needed:
```py
json_observations = [obs.to_dict() for obs in observations]
```

In a future release, these models will be fully integrated with API query functions. To preview these features, see {ref}`api-client`.

## API Recommended Practices
See [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
on iNaturalist for more general usage information and notes.
