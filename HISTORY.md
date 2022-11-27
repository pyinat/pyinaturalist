# History

## 0.18.0 (Unreleased)

### New Endpoints
* Added new **Observation** endpoint:
  * `get_observations_by_id()`
    * Replaces `get_observation`
    * Accepts multiple IDs
    * Uses a different endpoint (`GET /observations/{id}` instead of `GET /observations?id={id}`)`)
    * returns full term and value details for annotations

### Deprecated Endpoints
* `get_observation()` is now deprecated, and will be removed in a future release
  * Please use `get_observations()` or `get_observations_by_id()` instead

### Models
* Add `Observation.default_photo` property
* Use taxon icon as placeholder for `Observation.default_photo` if observation has no photos
* Update `Annotation` model to include controlled term and value details from updated `GET /observations/{id}` response format
* Add `Annotation.term` and `value` properties and init arguments for simpler initialization from term and value labels

### Sessions
* Fix JWT caching
* Add `cache_control` option to `ClientSession` to disable using Cache-Control headers for cache
  expiration (enabled by default)
* Add `urls_expire_after` option to `ClientSession` to update default cache expiration URL patterns

### Other Changes
* Fix `ObservationFieldValue` conversions for `date` and `datetime` fields
* Fix printing `Annotation` objects with `rich`
* Optionally use `ultrajson` instead of stdlib `json`, if installed
* Add `loop` argument to iNatClient and Paginator classes to allow passing an async event loop to be used for async iteration
* Add `Paginator.async_all()` method (async, non-blocking version of `.all()`)

## 0.17.4 (2022-07-11)
* Use a single data directory instead of separate 'cache' and 'user data' dirs
    * Platform-dependent; on Linux, for example, this will be `~/.local/share/pyinaturalist`

## 0.17.3 (2022-06-28)
* Add retries for requests that return invalid (truncated) JSON
* `max_retries` and `backoff_factor` arguments for `ClientSession` will apply to these retries (in
  addition to other request errors)

## 0.17.2 (2022-06-12)
* Handle nested 'photo' dictionaries when loading `Taxon.taxon_photos`
* Add model for `ListedTaxon.list`, and handle differences in format between `/taxa` and `/observations/{id}/taxon_summary`
* Minor fixes and improvements for creating and converting `Observation`, `Taxon`, and other model objects

## 0.17.1 (2022-05-20)
* Fix pagination bug causing only the first two pages of results to be returned
* Add Photo.uuid, observation_id, and user_id fields (for compatibility with inaturalist-open-data)
* Handle errors in ObservationField type conversions
* Improve terminal output for nested model objects (like `Observation.taxon`, `Taxon.ancestors`, etc.)
* If `Taxon.ancestor_ids` is missing, populate from either `ancestry` string or `ancestor` objects, if possible

## 0.17.0 (2022-05-17)
[See all Issues & PRs for 0.17](https://github.com/pyinat/pyinaturalist/milestone/8?closed=1)

### New Endpoints
* Added new **Observation** endpoint:
  * `get_observation_popular_field_values()`
* Added new **Project** endpoint and helper functions:
  * `update_project()`
  * `add_project_users()`
  * `delete_project_users()`

### Modified Endpoints
* Updated `get_projects_by_id()` to allow string values (URL slugs) for `project_id`
* Updated `get_user_by_id()` to allow string values (usernames) for `user_id`
* Added support for setting timeout for individual API requests (with `timeout` parameter)
* Added support for setting cache timeout for individual API requests (with `expire_after` parameter)
* Added support for bypassing the cache for individual API requests (with `refresh` parameter)

### Authentication
* Added support for JWT authentication, which will now be used by default
  * To get an OAuth access token instead of a JWT, call `get_access_token(jwt=False)`
* Added caching to `get_access_token()`. JWTs will be stored in the API response cache and reused
  until they expire.

### Models
* Remove default values from output when model objects are printed with `rich`
* Add `ControlledTermCount` model for use with `/observations/popular_field_values`
* `Photo`: Add `ext` and `mimetype` properties
* `Taxon`: Use icon in place of `default_photo` if missing

### Other Changes
* Dropped support for python 3.6
* Add an optional, abbreviated namespace `pyinat` as an alias for `pyinaturalist`
* Updated rate limiting with a SQLite-based backend. This adds persistence for rate limit tracking
  across multiple threads, processes, and/or application restarts. See
  [pyrate-limiter docs](https://github.com/vutran1710/PyrateLimiter#sqlite) for more details.
* Add a `clear_cache()` function for clearing cached API responses
* Misc improvements for response pretty-printing

## 0.16.0 (2022-02-22)
[See all Issues & PRs for 0.16](https://github.com/pyinat/pyinaturalist/milestone/7?closed=1)

### New Endpoints
* Added new **Taxon** endpoint: `get_taxa_map_layers()`
* Added new **Message** endpoints:
  * `get_messages()`
  * `get_message_by_id()`
  * `get_unread_meassage_count()`

### Observation Media
The following changes apply to `upload()`, `create_observation()`, and `update_observation()`:
* Added support for uploading observation photo & sound files from URLs
* Added support for attaching previously uploaded photos to an observation by photo ID

### Other Changes
* Added support for python 3.10
* Removed `pyinaturalist.user_agent` global variable and API function keyword args, and recommend setting on session object instead
* Removed `pyinaturalist.DRY_RUN*` global variables, and recommend setting in environment variables instead
* Fixed `count_only=True`/`per_page=0` to not run full query
* Do not error on unrecognized `**kwargs`, for cases where the API may accept some additional undocumented parameters
* Allow overriding default location for API request cache


## 0.15.0 (2021-09-07)
[See all Issues & PRs for 0.15](https://github.com/pyinat/pyinaturalist/milestone/6?closed=1)

### New Endpoints
* Added new functions for v1 **Observation** endpoints:
  * `create_observation()`
  * `update_observation()`
  * `delete_observation()`
  * `upload()` (uploads both photos and sounds)
  * These are now preferred over the older v0 endpoints
* Added new functions for v1 **Observation field value** endpoints:
  * `set_observation_field()` (creates and updates observation field values)
  * `delete_observation_field()`
* Added new function for **Observation taxon summary**: `get_observation_taxon_summary()`
* Added new functions for **Project observation** endpoints:
  * `add_project_observation()`
  * `delete_project_observation()`

### Modified Endpoints
* Added a `dry_run` argument to all API request functions to dry-run an individual request
* Added a `reverse` argument to all paginated API request functions to reverse the sort order

### Models
* Added new data models:
  * ListedTaxon
  * TaxonSummary
  * UserCounts
* Added a preview version of `iNatClient`, a higher-level interface for API requests, which returns
  model objects instead of JSON. See issues
  [#163](https://github.com/pyinat/pyinaturalist/issues/163) and
  [#217](https://github.com/pyinat/pyinaturalist/issues/217) for details.

### Performance
* Added API request caching with [requests-cache](https://github.com/reclosedev/requests-cache)
* Updated rate-limiting not apply to cached requests
* Added custom `ClientSession` class to configure caching, rate-limiting, retries, and timeouts

### Logging
* Improved logging output for dry-run mode: now shows formatted `PreparedRequest` details
  instead of `request()` keyword args
* Added an `enable_logging()` function to optionally show prettier logs with `rich`
* Updated logging to redact all credentials from logged API requests

### Other Changes
* Increased default timeout to 10 seconds to accomodate some longer-running queries
* Added `get_interval_ranges()` function to help with queries over a series of date/time intervals
* Fixed bug with `rule_details` param for `get_projects_by_id()`
* Added more tutorial/example notebooks

## 0.14.1 (2021-07-21)
* Added new function for **Posts** endpoint: `get_posts()`
* Fixed broken `response_format` parameter in `v0.get_observations()`

## 0.14.0 (2021-07-14)
[See all Issues & PRs for 0.14](https://github.com/pyinat/pyinaturalist/milestone/5?closed=1)

### New Endpoints
* Added new function for **Observation sounds** endpoint: `upload_sounds()`
* Added new function for **Life list** endpoint: `get_observation_taxonomy()`

### Modified Endpoints
* Added support for passing a `requests.Session` object to all API request functions
* Added a `photos` parameter `create_observation()` and `update_observation()` to upload photos
* Added a `sounds` parameter `create_observation()` and `update_observation()` to upload sounds
* Renamed `add_photo_to_observation()` to `upload_photos()`
  * The alias `rest_api.add_photo_to_observation()` is still available for backwards-compatibility
* Updated `upload_photos()` to take accept either a single photo or a list of photos, and return a list of responses
* Updated `upload_sounds()` to take accept either a single sound or a list of sounds, and return a list of responses
* Added alias `observed_on` for `observed_on_string` in `create_observation()`
* Fixed conversion for datetime parameters in `create_observation()` and `update_observation()`
* Updated all requests to correctly convert `datetime` objects to strings
* Moved API functions into separate modules by API version and resource type.
    * All can still be imported via `from pyinaturalist import *`
    * Added aliases for backwards-compatibility, so imports from `pyinaturalist.rest_api` and `pyinaturalist.node_api` will still work

### Deprecated Endpoints
* Deprecated `pyinaturalist.rest_api` module (moved to `pyinaturalist.v0` subpackage)
* Deprecated `pyinaturalist.node_api` module (moved to `pyinaturalist.v1` subpackage)
* Deprecated `get_geojson_observations()` (moved to join other observation conversion tools in `pyinaturalist-convert`)

### Models
Added data models for all API response types, to support working with typed python objects instead of JSON.

Models:
* Comment
* ControlledTerm
  * ControlledTermValue
  * Annotation
* Identification
* LifeList
    * LifeListTaxon
* Observation
* ObservationField
    * ObservationFieldValue
* Photo
* Place
* Project
    * ProjectObservation
    * ProjectObservationField
    * ProjectUser
* SearchResult
* Taxon
    * ConservationStatus
    * EstablishmentMeans
    * TaxonCount
    * TaxonCounts
* User

Model features:
* Type conversions
* Lazy initialization
* Basic formatters
* Table formatters

### Other Changes
* Consolidated response formatting into a single `pprint()` function (instead of one per resource type)
* Refactored and reorganized the following internal utility modules (see API docs for details):
    * `converters`
    * `docs`
    * `formatters`
    * `request_params`
* Added a default response timeout of 5 seconds
* Added an example (`examples/sample_responses.py`) containing response JSON, model objects, and tables of every type to experiment with
* Added a tutorial notebook (`examples/Tutorial.ipynb`)
* Set up pyinaturalist-notebook to be [runnable with Binder](https://mybinder.org/v2/gh/pyinat/pyinaturalist/main?filepath=examples)

-----
## 0.13.0 (2021-05-22)
[See all Issues & PRs for 0.13](https://github.com/pyinat/pyinaturalist/milestone/4?closed=1)

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
* Removed `node_api.get_all_observation_species_counts()`, since this was only added recently
* Updated `rest_api.get_observation_fields()` to return a dict with `'results'` for consistency with other endpoints

### Deprecated Endpoints
The following methods are now deprecated. They are still functional, but will raise a
  `DeprecationWarning`, and will be removed in a future release:
* `node_api.get_all_observations()`
* `rest_api.get_all_observation_fields()`

### Other Changes
* Added response formatting functions to `pyinaturalist.formatters`
* All API functions and formatters can now be imported from the top-level package, e.g.
  `from pyinaturalist import *`
* Removed `minify` option from `get_taxa_autocomplete`
* Published [pyinaturalist on conda-forge](https://anaconda.org/conda-forge/pyinaturalist)
* Added global rate-limiting to stay within the rates suggested in
  [API Recommended Practices](https://www.inaturalist.org/pages/api+recommended+practices)
  (per second, minute, and day)
* Moved `Dockerfile` and `docker-compose.yml` to a separate repo
  ([pyinaturalist-notebook](https://github.com/JWCook/pyinaturalist-notebook))
  and published on Docker Hub
* Packaging is now handled with Poetry. For users, installation still works the same. For developers,
  see [Contributing Guide](https://github.com/pyinat/pyinaturalist/blob/main/CONTRIBUTING.md) for details.

-----
## 0.12.1 (2021-03-07)
* Add undocumented `ident_user_id` parameter to `get_observations()`

## 0.12.0 (2021-02-02)
[See all Issues & PRs for 0.12](https://github.com/pyinat/pyinaturalist/milestone/3?closed=1)

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
## 0.11.0 (2020-11-04)
[See all Issues & PRs for 0.11](https://github.com/pyinat/pyinaturalist/milestone/2?closed=1)

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
* Dropped support for python 3.4
* Added support for python 3.9
* Added parameter validation for multiple-choice request parameters

## 0.10.0 (2020-06-16)
[See all Issues & PRs for 0.10](https://github.com/pyinat/pyinaturalist/milestone/1?closed=1)

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

* Bugfix: proper support for boolean and integer list parameters ([Issue #17](https://github.com/pyinat/pyinaturalist/issues/17))

## 0.9.0 (2020-05-06)

### New Endpoints
* Added new functions for Node API **Taxa** endpoints:

    * `node_api.get_taxa()`
    * `node_api.get_taxa_autocomplete()`
    * `node_api.get_taxa_by_id()`

## 0.8.0 (2019-07-11)

* All functions now take an optional `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ parameter in order to identify yourself to iNaturalist. If not set, `Pyinaturalist/<VERSION>` will be used.

## 0.7.0 (2019-05-08)

* `rest_api.delete_observation()` now raises `ObservationNotFound` if the observation doesn't exist
* minor dependencies update for security reasons

## 0.6.0 (2018-11-15)

* New function: `rest_api.delete_observation()`

## 0.5.0 (2018-11-05)

* New function: `node_api.get_observation()`

## 0.4.0 (2018-11-05)

* `create_observation()` now raises exceptions in case of errors.

## 0.3.0 (2018-11-05)

* `update_observation()` now raises exceptions in case of errors.

## 0.2.0 (2018-10-31)

* Better infrastructure (type annotations, documentation, ...)
* Dropped support for Python 2.
* New function: `update_observation()`
* `rest_api.AuthenticationError` is now `exceptions.AuthenticationError`

## 0.1.0 (2018-10-10)

* First release on PyPI.
