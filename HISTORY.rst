
History
-------

0.10.0 (2020-06-16)
^^^^^^^^^^^^^^^^^^^

* Added more info & examples to README for taxa endpoints, and other documentation improvements
* Added `minify` option to `node_api.get_taxa_autocomplete()`
* Added conversion for all date and datetime parameters to timezone-aware ISO 8601 timestamps
* Added a dry-run mode to mock out API requests for testing
* Added 6 additional observation response formats, including GeoJSON, Darwin Core, and others
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
