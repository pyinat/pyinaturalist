# History

## 0.14 (2021-TBD)
[See all Issues & PRs for 0.14](https://github.com/niconoe/pyinaturalist/milestone/5?closed=1)

* Set up pyinaturalist-notebook to [runnable with Binder](https://mybinder.org/v2/gh/niconoe/pyinaturalist/main?filepath=examples)
* Added models for all API response types, to support working with typed python objects instead of JSON
* Moved API functions into separate modules by API version and resource type.
    * All can still be imported via `from pyinaturalist import *`
    * Imports from `pyinaturalist.rest_api` and `pyinaturalist.node_api` will still work, but are
      deprecated and will be removed in a future release
* Update `create_observation()` and `update_observation()` to use `POST /observation_photos` endpoint to upload photos

-----
## 0.13 (2021-05-22)
[See all Issues & PRs for 0.13](https://github.com/niconoe/pyinaturalist/milestone/4?closed=1)

### New Endpoints
* Added new function for **Search** endpoint: `search()` (combined search for places, projects, taxa, and users)
* Added new functions for **Identifications** endpoints: `get_identifications()` and `get_identifications_by_id()`
* Added new functions for **Users** endpoints: `get_user_by_id()` and `get_users_autocomplete()`

### Modified Endpoints
* Added undocumented `ident_user_id` parameter to `get_observations()`
* Added `count_only=True` as an alias for `per_page=0` (to get only result counts).
* Added generic auto-pagination that can apply to any endpoint that supports pagination.
* Added `page='all'` as a shortcut for auto-pagination
* The above changes apply to all functions that support pagination:
  * `node_api.get_identifications()`
  * `node_api.get_observations()`
  * `node_api.get_observation_species_counts()`
  * `node_api.get_observation_observers()`
  * `node_api.get_observation_identifiers()`
  * `node_api.get_places_autocomplete()`
  * `node_api.get_projects()`
  * `node_api.get_taxa()`
  * `rest_api.get_observations()`
  * `rest_api.get_observation_fields()`
* The following methods are now deprecated. They are still functional, but will raise a `DeprecationWarning`:
  * `node_api.get_all_observations()`
  * `rest_api.get_all_observation_fields()`
* Removed `node_api.get_all_observation_species_counts()`, since this was only added recently
* Updated `rest_api.get_observation_fields()` to return a dict with `'results'` for consistency with other endpoints

### Response Formatting
* Removed `minify` option from `get_taxa_autocomplete`
* Added the following response formatting functions to `pyinaturalist.formatters`:
    * `format_controlled_terms()`
    * `format_identifications()`
    * `format_observations()`
    * `format_places()`
    * `format_projects()`
    * `format_species_counts()`
    * `format_taxa()`
    * `format_users()`
    * `simplify_observations()`

### Other Changes
* All API functions and formatters can now be imported from the top-level package, e.g.
  `from pyinaturalist import *`
* Published [pyinaturalist on conda-forge](https://anaconda.org/conda-forge/pyinaturalist)
* Added global rate-limiting to stay within the rates suggested in
  [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
  (per second, minute, and day)
* Moved `Dockerfile` and `docker-compose.yml` to a separate repo
  ([pyinaturalist-notebook](https://github.com/JWCook/pyinaturalist-notebook))
  and published on Docker Hub
* Packaging is now handled with Poetry. For users, installation still works the same. For developers,
  see [Contributing Guide](https://github.com/niconoe/pyinaturalist/blob/main/CONTRIBUTING.md) for details.

-----
### 0.12.1 (2021-03-07)
* Add undocumented `ident_user_id` parameter to `get_observations()`

## 0.12 (2021-02-02)
[See all Issues & PRs for 0.12](https://github.com/niconoe/pyinaturalist/milestone/3?closed=1)

### New Endpoints
* Added new function for **Observation Histogram** endpoint: `get_observation_histogram()`
* Added new function for **Observers** endpoint: `get_observation_observers()`
* Added new function for **Identifiers** endpoint: `get_observation_identifiers()`
* Added new function for **Controlled Terms** endpoints: `get_controlled_terms()`
    * Wraps both `GET /controlled_terms` and `/controlled_terms/for_taxon` endpoints

### Modified Endpoints
* Added conversion from date/time strings to timezone-aware python `datetime` objects.
  This applies to the following functions:
    * `node_api.get_observation()`
    * `node_api.get_observations()`
    * `node_api.get_all_observation()`
    * `node_api.get_projects()`
    * `node_api.get_projects_by_id()`
    * `node_api.get_taxa()`
    * `node_api.get_taxa_by_id()`
    * `rest_api.get_observation()`
    * `rest_api.get_observation_fields()`
    * `rest_api.get_all_observation_fields()`
* Added conversion for an additional `location` field in observation responses

### Authentication
* Added support for providing credentials via environment variables
* Added integration with system keyring for credentials storage
* Added documentation & examples for authentication options

### Other Changes
* Added a `Dockerfile` and `docker-compose.yml` for a Jupyter notebook containing pyinaturalist + other relevant packages
* Added some more detailed usage examples under `examples/`
* Improved performance for large paginated queries
* Fixed bug that dropped request parameter values of `0` as if they were `None`
* Dropped support for python 3.5
* Removed request parameters that were deprecated in 0.11

-----
## 0.11 (2020-11-04)
[See all Issues & PRs for 0.11](https://github.com/niconoe/pyinaturalist/milestone/2?closed=1)

### New Endpoints
* Added new functions for Node API **Places** endpoints:
    * `get_places_by_id()`
    * `get_places_nearby()`
    * `get_places_autocomplete()`
* Added new functions for Node API **Projects** endpoints:
    * `get_projects()`
    * `get_projects_by_id()`
* Added new function for an additional Node API **Observation** endpoint:
    * `get_observation_species_counts()`
    * `get_all_observation_species_counts()`

### Modified Endpoints
* Added support for simplified observation field syntax (`observation_fields={id: value}`)
  for `create_observations()` and `update_observation()`
* Updated `node_api.get_taxa_by_id()` to accept multiple IDs
* Updated `rest_api.get_observations()` with type conversion from strings to floats for response lat/long coordinates.
  Only applies to JSON response format.
* Updated `node_api.get_taxa_autocomplete()` with optional `min_rank` and `max_rank` parameters, for consistency with `get_taxa()`
* Using the `params` positional argument for the handful of functions that used it
  will raise a `DeprecationWarning`, but will otherwise still be functional until `0.12`
* Renamed `search_query` argument to `q` to be consistent with API request parameters
* Using the `search_query` argument for `rest_api.get_observation_fields()` and `rest_api.get_all_observation_fields()`
  will raise a `DeprecationWarning`, but will otherwise still be functional until `0.12`
* Renamed `create_observations()` to `create_observation()`, as this only supports creating a single observation per
  call. This is aliased to `create_observations()` for backwards-compatibility, but will raise a `DeprecationWarning`.

### Documentation & Usability
* Added example response data to docs all endpoints
* Added links to official API reference to docs for all endpoints
* Added full API request parameters to all API functions, in the form of keyword arguments with type annotations and docstrings
* Added complete table of iNaturalist API endpoints and endpoints implemented by pyinaturalist
* Added and improved usage examples
* Numerous other documentation improvements
* Made all API function signatures consistent by taking request params as keyword arguments

### Other Changes
* Dropped testing & support for python 3.4
* Added testing & support for python 3.9
* Added parameter validation for multiple-choice request parameters

## 0.10 (2020-06-16)
[See all Issues & PRs for 0.10](https://github.com/niconoe/pyinaturalist/milestone/1?closed=1)

### New Endpoints
* Added new **Observation** endpoint: `rest_api.get_observations()`, with 6 additional observation response formats, including GeoJSON, Darwin Core, and others

### Modified Endpoints
* Added `minify` option to `node_api.get_taxa_autocomplete()`

### Other Changes
* Added more info & examples to README for taxa endpoints, and other documentation improvements
* Added conversion for all date and datetime parameters to timezone-aware ISO 8601 timestamps
* Added a dry-run mode to mock out API requests for testing
* Set up pre-release builds for latest development version

-----
## 0.9.1 (2020-05-26)

* Bugfix: proper support for boolean and integer list parameters ([Issue #17](https://github.com/niconoe/pyinaturalist/issues/17))

## 0.9 (2020-05-06)

### New Endpoints
* Added new functions for Node API **Taxa** endpoints:

    * `node_api.get_taxa()`
    * `node_api.get_taxa_autocomplete()`
    * `node_api.get_taxa_by_id()`

## 0.8 (2019-07-11)

* All functions now take an optional `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ parameter in order to identify yourself to iNaturalist. If not set, `Pyinaturalist/<VERSION>` will be used.

## 0.7 (2019-05-08)

* `rest_api.delete_observation()` now raises `ObservationNotFound` if the observation doesn't exist
* minor dependencies update for security reasons

## 0.6 (2018-11-15)

* New function: `rest_api.delete_observation()`

## 0.5 (2018-11-05)

* New function: `node_api.get_observation()`

## 0.4 (2018-11-05)

* `create_observation()` now raises exceptions in case of errors.

## 0.3 (2018-11-05)

* `update_observation()` now raises exceptions in case of errors.

## 0.2 (2018-10-31)

* Better infrastructure (type annotations, documentation, ...)
* Dropped support for Python 2.
* New function: `update_observation()`
* `rest_api.AuthenticationError` is now `exceptions.AuthenticationError`

## 0.1 (2018-10-10)

* First release on PyPI.
