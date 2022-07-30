(user_guide)=
# {fa}`book` User Guide
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

:::{admonition} Python version compatibility
:class: toggle, tip

pyinaturalist currently requires **python 3.6+**. If you need to use an older version
of python, here are the last compatible versions of pyinaturalist:

* **python 2.7:** pyinaturalist 0.1
* **python 3.4:** pyinaturalist 0.10
* **python 3.5:** pyinaturalist 0.11
* **python 3.6:** still supported, but expected to be dropped in a future release
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
```{figure} images/inat-observation-page-annotated.png
```

And here is what that same observation looks like in JSON:
:::{admonition} Observation response JSON
:class: toggle
```{literalinclude} sample_data/get_observation_2.json
```
:::

### Previewing Responses
These responses can contain large amounts of response attributes, making it somewhat cumbersome if you
just want to quickly preview results (for example, in a Jupyter notebook). For that purpose, the
{py:func}`~pyinaturalist.formatters.pprint` function is included to format response data as a
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
```{figure} images/pprint_table.png
```
:::
::::

## Models
Data models ({py:mod}`pyinaturalist.models`) are included for all API response types. These allow
working with typed python objects instead of raw JSON. These are not used by default in the API query
functions, but you can easily use them as follows:
```python
>>> from pyinaturalist import Observation, get_observations
>>> response = get_observations(user_id='my_username)
>>> observations = Observation.from_json_list(response)
```

In a future release, these models will be fully integrated with the API query functions.

## Pagination
Most endpoints support pagination, using the parameters:
* `page`: Page number to get
* `per_page`: Number of results to get per page
* `count_only=True`: This is just a shortcut for `per_page=0`, which will return only the
  total number of results, not the results themselves.

The default and maximum `per_page` values vary by endpoint, but it's 200 for most endpoints.

To get all pages of results and combine them into a single response, use `page='all'`.
Note that this replaces the `get_all_*()` functions from pyinaturalist\<=0.12.

(auth)=

## Authentication
For any endpoints that create, update, or delete data, you will need to authenticate using an
OAuth2 access token. This requires both your iNaturalist username and password, and separate
"application" credentials.

:::{note} Read-only requests generally don't require authentication; however, if you want to access
private data visible only to your user (for example, obscured or private coordinates),
you will need to use an access token.
:::

**Summary:**
1. Create an iNaturalist application
2. Use {py:func}`.get_access_token` with your user + application credentials to get an access token
3. Pass that access token to any API request function that uses it

### Creating an Application
:::{admonition} Why do I need to create an application?
:class: toggle, tip

iNaturalist uses OAuth2, which provides several different methods (or "flows") to access the site.
For example, on the [login page](https://www.inaturalist.org/login), you have the option of logging
in with a username/password, or with an external provider (Google, Facebook, etc.):

```{image} images/inat-user-login.png
:alt: Login form
:width: 150
```

Outside of iNaturalist.org, anything else that uses the API to create or modify data is considered
an "application," even if you're just running some scripts on your own computer.

See [iNaturalist documentation](https://www.inaturalist.org/pages/api+reference#auth)
for more details on authentication.
:::

First, go to [New Application](https://www.inaturalist.org/oauth/applications/new) and fill out the
following pieces of information:

* **Name:** Any name you want to come up with. For example, if this is associated with a GitHub repo,
  you can use your repo name.
* **Description:** A brief description of what you'll be using this for. For example,
  *"Data access for my own observations"*.
* **Confidential:** ✔️ This should be checked.
* **URL and Redirect URI:** Just enter the URL to your GitHub repo, if you have one; otherwise any
  placeholder like "<https://www.inaturalist.org>" will work.

```{image} images/inat-new-application.png
:alt: New Application form
:width: 300
```

You should then see a screen like this, which will show your new application ID and secret. These will
only be shown once, so save them somewhere secure, preferably in a password manager.
```{image} images/inat-new-application-complete.png
:alt: Completed application form
:width: 400
```

### Basic Usage
There are a few different ways you can pass your credentials to iNaturalist. First, you can pass
them as keyword arguments to {py:func}`.get_access_token`:

```python
>>> from pyinaturalist import get_access_token
>>> access_token = get_access_token(
>>>     username='my_inaturalist_username',  # Username you use to login to iNaturalist.org
>>>     password='my_inaturalist_password',  # Password you use to login to iNaturalist.org
>>>     app_id='33f27dc63bdf27f4ca6cd95dd',  # OAuth2 application ID
>>>     app_secret='bbce628be722bfe2abde4',  # OAuth2 application secret
>>> )
```

### Environment Variables

You can also provide credentials via environment variables instead of arguments. The
environment variable names are the keyword arguments in uppercase, prefixed with `INAT_`:

* `INAT_USERNAME`
* `INAT_PASSWORD`
* `INAT_APP_ID`
* `INAT_APP_SECRET`

**Examples:**

::::{tab-set}
:::{tab-item} Python
:sync: python

```python
>>> import os
>>> os.environ['INAT_USERNAME'] = 'my_inaturalist_username'
>>> os.environ['INAT_PASSWORD'] = 'my_inaturalist_password'
>>> os.environ['INAT_APP_ID'] = '33f27dc63bdf27f4ca6cd95df'
>>> os.environ['INAT_APP_SECRET'] = 'bbce628be722bfe283de4'
```
:::
:::{tab-item} Unix (MacOS / Linux)
:sync: unix

```bash
export INAT_USERNAME="my_inaturalist_username"
export INAT_PASSWORD="my_inaturalist_password"
export INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
export INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
:::{tab-item} Windows CMD
:sync: cmd

```bat
set INAT_USERNAME="my_inaturalist_username"
set INAT_PASSWORD="my_inaturalist_password"
set INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
set INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
:::{tab-item} PowerShell
:sync: ps1

```powershell
$Env:INAT_USERNAME="my_inaturalist_username"
$Env:INAT_PASSWORD="my_inaturalist_password"
$Env:INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
$Env:INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
::::

Note that in any shell, these environment variables will only be set for your current shell
session. I.e., you can't set them in one terminal and then access them in another.

### Keyring Integration
To handle your credentials more securely, you can store them in your system keyring.
You could manually store and retrieve them with a utility like
[secret-tool](https://manpages.ubuntu.com/manpages/xenial/man1/secret-tool.1.html)
and place them in environment variables as described above, but there is a much simpler option.

Direct keyring integration is provided via [python keyring](https://github.com/jaraco/keyring). Most common keyring bakcends are supported, including:

* macOS [Keychain](https://en.wikipedia.org/wiki/Keychain_%28software%29)
* Freedesktop [Secret Service](http://standards.freedesktop.org/secret-service/)
* KDE [KWallet](https://en.wikipedia.org/wiki/KWallet)
* [Windows Credential Locker](https://docs.microsoft.com/en-us/windows/uwp/security/credential-locker)

To store your credentials in the keyring, run {py:func}`.set_keyring_credentials`:
```python
>>> from pyinaturalist.auth import set_keyring_credentials
>>> set_keyring_credentials(
>>>     username='my_inaturalist_username',
>>>     password='my_inaturalist_password',
>>>     app_id='33f27dc63bdf27f4ca6cd95df',
>>>     app_secret='bbce628be722bfe283de4',
>>> )
```

Afterward, you can call {py:func}`.get_access_token` without any arguments, and your credentials
will be retrieved from the keyring. You do not need to run {py:func}`.set_keyring_credentials`
again unless you change your iNaturalist password.

### Password Manager Integration
Keyring integration can be taken a step further by managing your keyring with a password
manager. This has the advantage of keeping your credentials in one place that can be synced
across multiple machines. [KeePassXC](https://keepassxc.org/) offers this feature for
macOS and Linux systems. See this guide for setup info:
[KeepassXC and secret service, a small walk-through](https://avaldes.co/2020/01/28/secret-service-keepassxc.html).

```{figure} images/password_manager_keying.png
Credentials storage with keyring + KeePassXC
```

## Sessions
If you want more control over how requests are sent, you can provide your own {py:class}`.ClientSession`
object using the `session` argument for any API request function.
See Caching and Rate-Limiting sections below for examples.

## Caching
All API requests are cached by default. These expire in 30 minutes for most endpoints, and
1 day for some infrequently-changing data (like taxa and places). See
[requests-cache: Expiration](https://requests-cache.readthedocs.io/en/latest/user_guide/expiration.html)
for details on cache expiration behavior.

You can change this behavior using {py:class}`.ClientSession`. For example, to keep cached requests for 5 days:
```python
>>> from datetime import timedelta
>>> from pyinaturalist import ClientSession, get_taxa
>>> session = ClientSession(expire_after=timedelta(days=5))
>>> get_taxa(q='warbler', locale=1, session=session)
```

To store the cache somewhere other than the default cache directory:
```python
>>> session = ClientSession(cache_name='~/data/api_requests.db')
```

To manually clear the cache:
```python
>>> session.cache.clear()
```

Or as a shortcut, without a session object:
```python
from pyinaturalist import clear_cache

clear_cache()
```

## Rate Limiting
Rate limiting is applied to all requests so they stay within the rates specified by iNaturalist's
[API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices).

You can modify these rate limits using {py:class}`.ClientSession`.
For example, to reduce the rate to 50 requests per minute:

```python
>>> from pyinaturalist import ClientSession, get_taxa
>>> session = ClientSession(per_minute=50)
>>> get_taxa(q='warbler', locale=1, session=session)
```

### Distributed Application Rate Limiting
The default rate-limiting backend is thread-safe, and persistent across application restarts. If
you have a larger application running from multiple processes, you will need an additional locking
mechanism to make sure these processes don't conflict with each other. This is available with
{py:class}`pyrate_limter.FileLockSQLiteBucket`, which can be passed as the session's `bucket_class`:

```python
>>> from pyinaturalist import ClientSession
>>> from pyrate_limter import FileLockSQLiteBucket
>>> session = ClientSession(bucket_class=FileLockSQLiteBucket)
```

This requires installing one additional dependency, [py-filelock](https://github.com/tox-dev/py-filelock):
```bash
pip install filelock
```

## Logging
You can configure logging for pyinaturalist using the standard Python `logging` module, for example
with {py:func}`logging.basicConfig`:
```python
>>> import logging
>>> logging.basicConfig()
>>> logging.getLogger('pyinaturalist').setLevel('INFO')
```

For convenience, an {py:func}`.enable_logging` function is included that will apply some recommended
settings, including colorized output (if viewed in a terminal) and better traceback formatting,
using the [rich](https://rich.readthedocs.io) library.
```python
>>> from pyinaturalist import enable_logging
>>> enable_logging()
```

## Dry-run mode
While developing and testing, it can be useful to temporarily mock out HTTP requests, especially
requests that add, modify, or delete real data. Pyinaturalist has some settings to make this easier.

### Dry-run individual requests
All API request functions take an optional `dry_run` argument. When set to `True`, requests will not
be sent but will be logged instead.

```{note}
You must enable at least INFO-level logging to see the logged request info
```
```python
>>> from pyinaturalist import get_taxa
>>> get_taxa(q='warbler', locale=1, dry_run=True)
{'results': [], 'total_results': 0}
[07-26 18:55:50] INFO  Request: GET https://api.inaturalist.org/v1/taxa?q=warbler&locale=1
User-Agent: pyinaturalist/0.15.0
Accept: application/json
```

### Dry-run all requests
To enable dry-run mode for all requests, set the `DRY_RUN_ENABLED` environment variable:

::::{tab-set}
:::{tab-item} Python
:sync: python

```python
>>> import os
>>> os.environ['DRY_RUN_ENABLED'] = 'true'
```
:::
:::{tab-item} Unix (MacOS / Linux)
:sync: unix

```bash
export DRY_RUN_ENABLED=true
```
:::
:::{tab-item} Windows CMD
:sync: cmd

```bat
set DRY_RUN_ENABLED="true"
```
:::
:::{tab-item} PowerShell
:sync: ps1

```powershell
$Env:DRY_RUN_ENABLED="true"
```
:::
::::


### Dry-run only write requests
If you would like to send real `GET` requests but mock out any requests that modify data
(`POST`, `PUT`, and `DELETE`), you can use the `DRY_RUN_WRITE_ONLY` variable instead:

::::{tab-set}
:::{tab-item} Python
:sync: python

```python
>>> import os
>>> os.environ['DRY_RUN_WRITE_ONLY'] = 'true'
```
:::
:::{tab-item} Unix (MacOS / Linux)
:sync: unix

```bash
export DRY_RUN_WRITE_ONLY=true
```
:::
:::{tab-item} Windows CMD
:sync: cmd

```bat
set DRY_RUN_WRITE_ONLY="true"
```
:::
:::{tab-item} PowerShell
:sync: ps1

```powershell
$Env:DRY_RUN_WRITE_ONLY="true"
```
:::
::::

## User Agent
If you're using the API as part of a project or application, it's good practice to add that info to
the [user-agent](https://en.wikipedia.org/wiki/User_agent). You can optionally set this on the
session object used to make requests:

```python
>>> from pyinaturalist import ClientSession
>>> session = ClientSession(user_agent='my_app/1.0.0')
```

## API Recommended Practices
See [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
on iNaturalist for more general usage information and notes.
