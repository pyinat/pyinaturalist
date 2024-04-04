# Advanced Usage
This page describes some advanced features of pyinaturalist.

## Authentication
See {ref}`auth` for details on using authenticated endpoints.

## Pagination
Most endpoints support pagination, using the parameters:
* `page`: Page number to get
* `per_page`: Number of results to get per page
* `count_only=True`: This is just a shortcut for `per_page=0`, which will return only the
  total number of results, not the results themselves.

The default and maximum `per_page` values vary by endpoint, but it's 200 for most endpoints.

To get all pages of results and combine them into a single response, use `page='all'`.
Note that this replaces the `get_all_*()` functions from pyinaturalist\<=0.12.

## Sessions
If you want more control over how requests are sent, you can provide your own {py:class}`.ClientSession`
object using the `session` argument for any API request function:
```python
>>> from pyinaturalist import ClientSession
>>> session = ClientSession(...)
>>> request_function(..., session=session)
```

## Caching
All API requests are cached by default. These expire in 30 minutes for most endpoints, and
1 day for some infrequently-changing data (like taxa and places). See
[requests-cache: Expiration](https://requests-cache.readthedocs.io/en/stable/user_guide/expiration.html)
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

## Timeouts
If you are seeing frequent timeouts (`TimeoutError`) due to iNat server problems or a slow internet
connection, you can increase the timeout (default: 20 seconds):
```python
>>> from pyinaturalist import ClientSession
>>> session = ClientSession(timeout=40)
```

## Retries
Similarly, if you are seeing intermittent non-timeout errors due to server issues, you can adjust
the number of times to retry failed requests (default: 5):
```python
>>> from pyinaturalist import ClientSession
>>> session = ClientSession(retries=7)
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

Float values also work, for example to slow it down to less than 1 request per second):
```python
>>> session = ClientSession(per_second=0.5)
```

### Distributed Application Rate Limiting
The default rate-limiting backend is thread-safe, and persistent across application restarts. If
you have a larger application running from multiple processes, you will need an additional locking
mechanism to make sure these processes don't conflict with each other. This is available with
{py:class}`.FileLockSQLiteBucket`, which can be passed as the session's `bucket_class`:

```python
>>> from pyinaturalist import ClientSession, FileLockSQLiteBucket
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
