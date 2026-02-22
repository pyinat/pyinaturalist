# Quickstart
Here are usage examples for some of the most commonly used features.

First, install with pip:
```bash
pip install pyinaturalist
```

Then, import the main API functions:
```python
from pyinaturalist import *
```

## Search observations
Let's start by searching for all your own observations. There are
[numerous fields you can search on](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.get_observations), but we'll just use `user_id` for now:
```python
>>> observations = get_observations(user_id='my_username')
```

The full response will be in JSON format, but we can use `pyinaturalist.pprint()` to print out a summary:
```python
>>> pprint(observations)
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

## Create and update observations
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
See [Authentication](https://pyinaturalist.readthedocs.io/en/stable/authentication.md)
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
    sounds=['~/observations/recording.mp3'],
)

# Save the new observation ID
new_observation_id = response[0]['id']
```

We can then [update the observation](https://pyinaturalist.readthedocs.io/en/stable/modules/pyinaturalist.v1.observations.html#pyinaturalist.v1.observations.update_observation) information, photos, or sounds:
```python
update_observation(
    new_observation_id,
    access_token=token,
    description='updated description !',
    photos='~/observations/wasp_nest.jpg',
    sounds='~/observations/wasp_nest.mp3',
)
```

## Search species
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
