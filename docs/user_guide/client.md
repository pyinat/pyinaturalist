(api-client)=
# API Client Class
In addition to the lower-level API wrapper functions, pyinaturalist provides {py:class}`.iNatClient`, a higher-level, object-oriented interface. It adds the following features:
* Returns fully typed {ref}`model objects <data-models>` instead of JSON
* Easier to configure
* Easier to paginate large responses
* Basic async support

## Basic usage
All API calls are available as methods on {py:class}`.iNatClient`, grouped by resource type. For example:
* Annotation requests: {py:class}`iNatClient.annotations <.AnnotationController>`
* Identification requests: {py:class}`iNatClient.identifications <.IdentificationController>`
* Observation requests: {py:class}`iNatClient.observations <.ObservationController>`
* Place requests: {py:class}`iNatClient.places <.PlaceController>`
* Project requests: {py:class}`iNatClient.projects <.ProjectController>`
* Unified search: {py:class}`iNatClient.search <.SearchController>`
* Taxon requests: {py:class}`iNatClient.taxa <.TaxonController>`
* User requests: {py:class}`iNatClient.users <.UserController>`

These resource groups are referred to elsewhere in the docs as **controllers.**  See :ref:`Controller classes <controllers>` for more info.

The main observation search is available in `client.observations.search()`.
Here is an example of searching for observations by taxon name:

```py
 >>> from pyinaturalist import iNatClient
 >>> client = iNatClient()
 >>> observations = client.observations.search(user_id='my_username', taxon_name='Danaus plexippus').all()
 ```

(pagination)=
## Pagination
Most client methods return a {py:class}`.Paginator` object. This is done so we can both:
* Make it easy to fetch multiple (or all) pages of a large request, and
* Avoid fetching more data than needed.

Paginators can be iterated over like a normal collection, and new pages will be fetched as they are needed:
```py
for obs in client.observations.search(user_id='my_username', taxon_name='Danaus plexippus'):
    print(obs)
```

You can get all results at once with `.all()`:
```py
query = client.observations.search(user_id='my_username', taxon_name='Danaus plexippus')
observations = query.all()
```

Or get only up to a certain number of results with `.limit()`:
```py
observations = query.limit(500)
```

You can get only the first result with `.one()`:
```py
observation = query.one()
```

Or only the total number of results (without fetching any of them) with `.count()`:
```py
print(query.count())
```

## Single-ID requests
For most controllers, there is a shortcut to get a single object by ID, by calling the controller as a method with a single argument. For example, to get an observation by ID:
```py
observation = client.observations(12345)
```

## Authentication
Add credentials needed for {ref}`authenticated requests <auth>`:
Note: Passing credentials via environment variables or keyring is preferred

```py
>>> creds = {
...     'username': 'my_inaturalist_username',
...     'password': 'my_inaturalist_password',
...     'app_id': '33f27dc63bdf27f4ca6cd95dd9dcd5df',
...     'app_secret': 'bbce628be722bfe2abd5fc566ba83de4',
... }
>>> client = iNatClient(creds=creds)
```

## Default request parameters
There are some parameters that several different API endpoints have in common, and in some cases you may want to always use the same value. As a shortcut for this, you can pass these common parameters and their values via `default_params`.

For example, a common use case for this is to add `locale` and `preferred_place_id`:
```python
>>> default_params={'locale': 'en', 'preferred_place_id': 1}
>>> client = iNatClient(default_params=default_params)
```

These parameters will then be automatically used for any endpoints that accept them.

## Caching, Rate-limiting, Timeouts, and Retries
See :py:class:`.ClientSession` and :ref:`advanced` for details on these settings.

`iNatClient` will accept any arguments for `ClientSession`, for example:
```py
>>> client = iNatClient(per_minute=50, expire_after=3600, timeout=30, retries=3)
```

Or you can provide your own session object:

```py
>>> session = MyCustomSession(encabulation_factor=47.2)
>>> client = iNatClient(session=session)
```

## Updating settings
All settings can also be modified after creating the client:
```py
>>> client.session = ClientSession()
>>> client.creds['username'] = 'my_inaturalist_username'
>>> client.default_params['locale'] = 'es'
>>> client.dry_run = True
```

## Async usage
Most client methods can be used in an async application without blocking the event loop. Paginator objects can be used as an async iterator:
```py
async for obs in client.observations.search(user_id='my_username'):
    print(obs)
```

Or to get all results at once, use {py:meth}`Paginator.async_all`:
```py
query = client.observations.search(user_id='my_username')
observations = await query.async_all()
```


## Controller methods
This section lists all the methods available on each controller.
