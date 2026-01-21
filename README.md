# pyinaturalist

[![Build](https://github.com/pyinat/pyinaturalist/actions/workflows/build.yml/badge.svg)](https://github.com/pyinat/pyinaturalist/actions)
[![Codecov](https://codecov.io/gh/pyinat/pyinaturalist/branch/main/graph/badge.svg)](https://codecov.io/gh/pyinat/pyinaturalist)
[![Documentation](https://img.shields.io/readthedocs/pyinaturalist/stable)](https://pyinaturalist.readthedocs.io)

[![PyPI](https://img.shields.io/pypi/v/pyinaturalist?color=blue)](https://pypi.org/project/pyinaturalist)
[![Conda](https://img.shields.io/conda/vn/conda-forge/pyinaturalist?color=blue)](https://anaconda.org/conda-forge/pyinaturalist)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/pyinaturalist)](https://pypi.org/project/pyinaturalist)

[![Run with Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyinat/pyinaturalist/main?urlpath=lab/tree/examples)

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
* ⬅️ **Convenient responses:** Type conversions to the things you would expect in python, and
  typed model objects (`Observation`, `Taxon`, etc.) with full IDE autocompletion
* 🔒 **Security:** Keyring integration for secure credential storage
* 📗 **Docs:** Example requests, responses, scripts, and Jupyter notebooks to help get you started
* 🧪 **Testing:** A dry-run testing mode to preview your requests before potentially modifying data
* 💚 **Responsible use:** Follows the
  [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices) without extra configuration;
  caching and rate-limiting features reduce bandwidth usage, errors, and unexpected throttling

### Supported Endpoints
Many of the most relevant API endpoints are supported, including:
* 📝 Annotations and observation fields
* 🆔 Identifications
* 💬 Messages
* 👀 Observations (multiple formats)
* 📷 Observation photos + sounds
* 📊 Observation histograms, observers, identifiers, life lists, and species counts
* 📍 Places
* 👥 Projects
* 🐦 Species
* 👤 Users

## Quickstart
Here are usage examples for some of the most commonly used features.

First, install with pip:
```bash
pip install pyinaturalist
```

Then, import and create a client object. This will be our main interface to the API:
```python
from pyinaturalist import *
client = iNatClient()
```

```{note}
If you are looking for the lower-level API functions (without the client class), see [this page](docs/user_guide/quickstart_v0.md)
```

### Search observations
Let's start by searching for all your own observations. There are
[numerous fields you can search on](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.ObservationController.html#pyinaturalist.controllers.ObservationController.search), but we'll just use `user_id` for now:
```python
>>> results = client.observations.search(user_id='my_username')
```

The full response consists of [`Observation`](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.models.Observation.html) objects with numerous attributes, but we can use `pyinaturalist.pprint()` to print
out a condensed summary:
```python
>>> pprint(results)
ID         Taxon                               Observed on   User     Location
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
117585709  Genus: Hyoscyamus (henbanes)        May 18, 2022  niconoe  Calvi, France
117464920  Genus: Omophlus                     May 17, 2022  niconoe  Galéria, France
117464393  Genus: Briza (Rattlesnake Grasses)  May 17, 2022  niconoe  Galéria, France
...
```

You can also get
[observation counts by species](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.ObservationController.html#pyinaturalist.controllers.ObservationController.species_counts).
On iNaturalist.org, this information can be found on the 'Species' tab of search results.
For example, to get species counts of all your own research-grade observations:
```python
>>> counts = client.observations.species_counts(user_id='my_username', quality_grade='research')
>>> pprint(counts)
 ID     Rank      Scientific name               Common name             Count
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
47934   species   🐛 Libellula luctuosa         Widow Skimmer           7
48627   species   🌻 Echinacea purpurea         Purple Coneflower       6
504060  species   🍄 Pleurotus citrinopileatus  Golden Oyster Mushroom  6
...
```

The data will be in the form of
[`TaxonCount`](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.models.TaxonCount.html)
objects:
```python
>>> counts[0]
TaxonCount(
    id=48662,
    name='Danaus plexippus',
    preferred_common_name='Monarch',
    rank='species',
    count=13,
    observations_count=458712,
    ...
)
```

Another useful format is the
[observation histogram](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.ObservationController.html#pyinaturalist.controllers.ObservationController.histogram),
which shows the number of observations over a given time interval. The default is `month_of_year`:
```python
>>> histogram = client.observations.histogram(user_id='my_username')
>>> pprint(histogram)
Month   Count
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Jan     8       ████
Feb     1       █
Mar     20      ██████████
```

The raw data will be a dict, with either `int` or `datetime` keys, depending on the interval:
```python
>>> print(histogram.raw)
{
    1: 8,  # January
    2: 1,  # February
    3: 19, # March
    ...,   # etc.
}
```

### Create and update observations: authentication
To create or modify observations, you will first need to log in.
This requires creating an [iNaturalist app](https://www.inaturalist.org/oauth/applications/new),
which will be used to get an access token.
```python
creds = {
    'username': 'my_username',
    'password': 'my_password',
    'app_id': 'my_app_id',
    'app_secret': 'my_app_secret',
}
client = iNatClient(creds=creds)
```

See [Authentication](https://pyinaturalist.readthedocs.io/en/stable/authentication.html)
for more options including environment variables, keyrings, and password managers.
A keyring is recommended, which does not require passing credentials directly:
```python
client = iNatClient()
# Creds will be requested from the keyring when an authenticated request is made
client.observations.create(...)
```

### Create and update observations
Now we can [create a new observation](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.ObservationController.html#pyinaturalist.controllers.ObservationController.create):
```python
from datetime import datetime

new_obs = client.observations.create(
    taxon_id=54327,  # Vespa Crabro
    observed_on_string=datetime.now(),
    time_zone='Brussels',
    description='This is a free text comment for the observation',
    tag_list='wasp, Belgium',
    latitude=50.647143,
    longitude=4.360216,
    positional_accuracy=50,  # GPS accuracy in meters
    photos=['~/observations/wasp1.jpg', '~/observations/wasp2.jpg'],
    sounds=['~/observations/recording.wav'],
)
```

We can then [update the observation](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.ObservationController.html#pyinaturalist.controllers.ObservationController.update) information, photos, or sounds:
```python
client.observations.update(
    new_obs.id,  # Use the observation ID from the result above
    access_token=token,
    description='updated description !',
    photos='~/observations/wasp_nest.jpg',
    sounds='~/observations/wasp_nest.mp3',
)
```

### Search species
There are many more resource types available besides observations. Taxonomy is another useful one.

Let's say you partially remember either a genus or family name that started with **'vespi'**-something.
The [taxon search](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.controllers.TaxonController.html#pyinaturalist.controllers.TaxonController.search)
can be used to search by name, rank, and several other criteria:
```python
>>> results = client.taxa.search(q='vespi', rank=['genus', 'family'])
```

As with observations, there is a lot of information available in the response ([`Taxon`](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.models.Taxon.html#pyinaturalist.models.Taxon) objects), but we'll print just a few basic details:
```python
>>> pprint(results)
ID        Rank     Scientific name    Common name
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
52747     family   🐝 Vespidae        Hornets, Paper Wasps, Potter Wasps, and Allies
84737     genus    🦋 Vespina
646195    genus    🪰 Vespiodes
...
```

## Next Steps
For more information, see:

* [User Guide](https://pyinaturalist.readthedocs.io/en/stable/user_guide/index.html):
  introduction and general features that apply to most endpoints
* [Endpoint Summary](https://pyinaturalist.readthedocs.io/en/stable/endpoints.html):
  a complete list of endpoints wrapped by pyinaturalist
* [Examples](https://pyinaturalist.readthedocs.io/en/stable/examples.html):
  data visualizations and other examples of things to do with iNaturalist data
* [Reference](https://pyinaturalist.readthedocs.io/en/stable/reference.html): Detailed API documentation
* [Contributing Guide](https://pyinaturalist.readthedocs.io/en/stable/contributing.html):
  development details for anyone interested in contributing to pyinaturalist
* [History](https://github.com/pyinat/pyinaturalist/blob/dev/HISTORY.md):
  details on past and current releases
* [Issues](https://github.com/pyinat/pyinaturalist/issues): planned & proposed features

## Feedback
If you have any problems, suggestions, or questions about pyinaturalist, you are welcome to [create an issue](https://github.com/pyinat/pyinaturalist/issues/new/choose) or [discussion](https://github.com/orgs/pyinat/discussions). Also, **PRs are welcome!**

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
