# pyinaturalist

[![Build](https://github.com/pyinat/pyinaturalist/workflows/Build/badge.svg)](https://github.com/pyinat/pyinaturalist/actions)
[![Codecov](https://codecov.io/gh/pyinat/pyinaturalist/branch/main/graph/badge.svg)](https://codecov.io/gh/pyinat/pyinaturalist)
[![Documentation](https://img.shields.io/readthedocs/pyinaturalist/stable)](https://pyinaturalist.readthedocs.io)

[![PyPI](https://img.shields.io/pypi/v/pyinaturalist?color=blue)](https://pypi.org/project/pyinaturalist)
[![Conda](https://img.shields.io/conda/vn/conda-forge/pyinaturalist?color=blue)](https://anaconda.org/conda-forge/pyinaturalist)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/pyinaturalist)](https://pypi.org/project/pyinaturalist)

[![Run with Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyinat/pyinaturalist/main?urlpath=lab/tree/examples)
[![Open in VSCode](docs/images/open-in-vscode.svg)](https://open.vscode.dev/pyinat/pyinaturalist)

<br/>

[![](docs/images/pyinaturalist_logo_med.png)](https://pyinaturalist.readthedocs.io)

# Introduction
[**iNaturalist**](https://www.inaturalist.org) is a community science platform that helps people
get involved in the natural world by observing and identifying the living things around them.
Collectively, the community produces a rich source of global biodiversity data that can be valuable
to anyone from hobbyists to scientists.

**pyinaturalist** is a client for the [iNaturalist API](https://api.inaturalist.org/v1) that makes
these data easily accessible in the python programming language.

- [Features](#features)
- [Quickstart](#quickstart)
- [Next Steps](#next-steps)
- [Feedback](#feedback)
- [Related Projects](#related-projects)

## Features
* ➡️ **Easier requests:** Simplified request formats, easy pagination, and complete request
  parameter type annotations for better IDE integration
* ⬅️ **Convenient responses:** Type conversions to the things you would expect in python, and an
  optional object-oriented inteface for response data
* 🔒 **Security:** Keyring integration for secure credential storage
* 📗 **Docs:** Example requests, responses, scripts, and Jupyter notebooks to help get you started
* 💚 **Responsible use:** Follows the
  [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
  by default, so you can be nice to the iNaturalist servers and not worry about rate-limiting errors
* 🧪 **Testing:** A dry-run testing mode to preview your requests before potentially modifying data

### Supported Endpoints
Many of the most relevant API endpoints are supported, including:
* 📝 Annotations and observation fields
* 🆔 Identifications
* 💬 Messages
* 👀 Observations (multiple formats)
* 📷 Observation photos + sounds
* 📊 Observation observers, identifiers, histograms, life lists, and species counts
* 📍 Places
* 👥 Projects
* 🐦Species
* 👤 Users

## Quickstart
Here are usage examples for some of the most commonly used features.

First, install with pip:
```bash
pip install pyinaturalist
```

Then, import the main API functions:
```python
from pyinaturalist import *
```

### Search observations
Let's start by searching for all your own observations. There are
[numerous fields you can search on](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.create_observation), but we'll just use `user_id` for now:
```python
>>> observations = get_observations(user_id='my_username')
```

The full response will be in JSON format, but we can use `pyinaturalist.pprint()` to print out a summary:
```python
>>> for obs in observations['results']:
>>>    pprint(obs)
ID         Taxon                               Observed on   User     Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
117585709  Genus: Hyoscyamus (henbanes)        May 18, 2022  niconoe  Calvi, France
117464920  Genus: Omophlus                     May 17, 2022  niconoe  Galéria, France
117464393  Genus: Briza (Rattlesnake Grasses)  May 17, 2022  niconoe  Galéria, France
...
```

You can also get
[observation counts by species](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.get_observation_species_counts).
On iNaturalist.org, this information can be found on the 'Species' tab of search results.
For example, to get species counts of all your own research-grade observations:
```python
>>> counts = get_observation_species_counts(user_id='my_username', quality_grade='research')
>>> pprint(counts)
 ID     Rank      Scientific name               Common name             Count
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
47934   species   🐛 Libellula luctuosa         Widow Skimmer           7
48627   species   🌻 Echinacea purpurea         Purple Coneflower       6
504060  species   🍄 Pleurotus citrinopileatus  Golden Oyster Mushroom  6
...
```

Another useful format is the
[observation histogram](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.get_observation_histogram),
which shows the number of observations over a given interval. The default is `month_of_year`:
```python
>>> histogram = get_observation_histogram(user_id='my_username')
>>> print(histogram)
{
    1: 8,  # January
    2: 1,  # February
    3: 19, # March
    ...,   # etc.
}
```

### Create and update observations
To create or modify observations, you will first need to log in.
This requires creating an [iNaturalist app](https://www.inaturalist.org/oauth/applications/new),
which will be used to get an access token.
```python
token = get_access_token(
    username='my_username',
    password='my_password',
    app_id='my_app_id',
    app_secret='my_app_secret',
)
```
See [Authentication](https://pyinaturalist.readthedocs.io/en/latest/user_guide.html#authentication)
for more options including environment variables, keyrings, and password managers.

Now we can [create a new observation](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.create_observation):
```python
from datetime import datetime

response = create_observation(
    taxon_id=54327,  # Vespa Crabro
    observed_on_string=datetime.now(),
    time_zone='Brussels',
    description='This is a free text comment for the observation',
    tag_list='wasp, Belgium',
    latitude=50.647143,
    longitude=4.360216,
    positional_accuracy=50,  # GPS accuracy in meters
    access_token=token,
    photos=['~/observations/wasp1.jpg', '~/observations/wasp2.jpg'],
)

# Save the new observation ID
new_observation_id = response[0]['id']
```

We can then [update the observation](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.update_observation) information, photos, or sounds:
```python
update_observation(
    17932425,
    access_token=token,
    description='updated description !',
    photos='~/observations/wasp_nest.jpg',
    sounds='~/observations/wasp_nest.mp3',
)
```

### Search species
Let's say you partially remember either a genus or family name that started with **'vespi'**-something.
The [taxa endpoint](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.taxa.html#pyinaturalist.v1.taxa.get_taxa)
can be used to search by name, rank, and several other criteria
```python
>>> response = get_taxa(q='vespi', rank=['genus', 'family'])
```

As with observations, there is a lot of information in the response, but we'll print just a few basic details:
```python
>>> pprint(response)
[52747] Family: Vespidae (Hornets, Paper Wasps, Potter Wasps, and Allies)
[92786] Genus: Vespicula
[84737] Genus: Vespina
...
```

## Next Steps
For more information, see:

* [User Guide](https://pyinaturalist.readthedocs.io/en/latest/user_guide.html):
  introduction and general features that apply to most endpoints
* [Endpoint Summary](https://pyinaturalist.readthedocs.io/en/latest/endpoints.html):
  a complete list of endpoints wrapped by pyinaturalist
* [Examples](https://pyinaturalist.readthedocs.io/en/stable/examples.html):
  data visualizations and other examples of things to do with iNaturalist data
* [Reference](https://pyinaturalist.readthedocs.io/en/latest/reference.html): Detailed API documentation
* [Contributing Guide](https://pyinaturalist.readthedocs.io/en/stable/contributing.html):
  development details for anyone interested in contributing to pyinaturalist
* [History](https://github.com/pyinat/pyinaturalist/blob/dev/HISTORY.md):
  details on past and current releases
* [Issues](https://github.com/pyinat/pyinaturalist/issues): planned & proposed features

## Feedback
If you have any problems, suggestions, or questions about pyinaturalist, please let us know!
Just [create an issue](https://github.com/pyinat/pyinaturalist/issues/new/choose).
Also, **PRs are welcome!**

**Note:** pyinaturalist is developed by members of the iNaturalist community, and is not endorsed by
iNaturalist.org or the California Academy of Sciences. If you have non-python-specific questions
about the iNaturalist API or iNaturalist in general, the
[iNaturalist Community Forum](https://forum.inaturalist.org/) is the best place to start.

## Related Projects
Other python projects related to iNaturalist:

* [naturtag](https://github.com/pyinat/naturtag): A desktop application for tagging image files with iNaturalist taxonomy & observation metadata
* [pyinaturalist-convert](https://github.com/pyinat/pyinaturalist-convert): Tools to convert observation data to and from a variety of useful formats
* [pyinaturalist-notebook](https://github.com/pyinat/pyinaturalist-notebook): Jupyter notebook Docker image for pyinaturalist
* [dronefly](https://github.com/dronefly-garden/dronefly): A Discord bot with iNaturalist integration, used by the iNaturalist Discord server.
