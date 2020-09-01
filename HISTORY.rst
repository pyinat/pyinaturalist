
History
-------

0.11.0 (2020-TBD)
^^^^^^^^^^^^^^^^^

* Dropped support for python 3.4
* Added new functions for Node API Places endpoints: ``get_places_by_id()``, ``get_places_nearby()``, ``get_places_autocomplete()``
* Updated ``node_api.get_taxa_by_id()`` to accept multiple IDs
* Updated ``rest_api.get_observations()`` with type conversion from strings to floats for response lat/long coordinates.
  Only applies to JSON response format.
* Added new function for an additional Observation endpoint: ``node_api.get_observation_species_counts()``
* Updated ``node_api.get_taxa_autocomplete()`` with optional ``min_rank`` and ``max_rank`` parameters, for consistency with ``get_taxa()``
* Added full API request parameters to all API functions, in the form of keyword arguments with type annotations and docstrings
* Added links to official API docs for each endpoint
* Added parameter validation for multiple-choice request parameters
* Made all API function signatures consistent by taking request params as keyword arguments
* Using the ``params`` positional argument for the handful of functions that used it
  will raise a ``DeprecationWarning``, but will otherwise still be functional until ``0.12``
* Renamed ``search_query`` argument to ``q`` to be consistent with API request parameters
* Using the ``search_query`` argument for ``rest_api.get_observation_fields()`` and ``rest_api.get_all_observation_fields()``
  will raise a ``DeprecationWarning``, but will otherwise still be functional until ``0.12``

0.10.0 (2020-06-16)
^^^^^^^^^^^^^^^^^^^

* Added more info & examples to README for taxa endpoints, and other documentation improvements
* Added ``minify`` option to ``node_api.get_taxa_autocomplete()``
* Added conversion for all date and datetime parameters to timezone-aware ISO 8601 timestamps
* Added a dry-run mode to mock out API requests for testing
* Added ``rest_api.get_observations()`` with 6 additional observation response formats, including GeoJSON, Darwin Core, and others
* Set up pre-release builds for latest development version

0.9.1 (2020-05-26)
^^^^^^^^^^^^^^^^^^

* Bugfix: proper support for boolean and integer list parameters (see https://github.com/niconoe/pyinaturalist/issues/17). Thanks Jordan Cook!

0.9.0 (2020-05-06)
^^^^^^^^^^^^^^^^^^

* new taxa-related functions: node_api.get_taxa(), node_api.get_taxa_autocomplete(), node_api.get_taxa_by_id(). Many thanks to Jordan Cook!

0.8.0 (2019-07-11)
^^^^^^^^^^^^^^^^^^

* all functions now take an optional `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ parameter in order to identify yourself to iNaturalist. If not set, `Pyinaturalist/<VERSION>` will be used.

0.7.0 (2019-05-08)
^^^^^^^^^^^^^^^^^^

* rest_api.delete_observation() now raises ObservationNotFound if the observation doesn't exists
* minor dependencies update for security reasons

0.6.0 (2018-11-15)
^^^^^^^^^^^^^^^^^^

* New function: rest_api.delete_observation()

0.5.0 (2018-11-05)
^^^^^^^^^^^^^^^^^^

* New function: node_api.get_observation()

0.4.0 (2018-11-05)
^^^^^^^^^^^^^^^^^^

* create_observation() now raises exceptions in case of errors.

0.3.0 (2018-11-05)
^^^^^^^^^^^^^^^^^^

* update_observation() now raises exceptions in case of errors.

0.2.0 (2018-10-31)
^^^^^^^^^^^^^^^^^^

* Better infrastructure (type annotations, documentation, ...)
* Dropped support for Python 2.
* New function: update_observation()
* rest_api.AuthenticationError is now exceptions.AuthenticationError


0.1.0 (2018-10-10)
^^^^^^^^^^^^^^^^^^

* First release on PyPI.
