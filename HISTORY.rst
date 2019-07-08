.. :changelog:

History
-------

Current
+++++++

* all functions now take an optional `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ parameter in order to identify yourself to iNaturalist. If not set, `Pyinaturalist <VERSION>` will be used.

0.7.0 (2019-05-08)
++++++++++++++++++

* rest_api.delete_observation() now raises ObservationNotFound if the observation doesn't exists
* minor dependencies update for security reasons

0.6.0 (2018-11-15)
++++++++++++++++++

* New function: rest_api.delete_observation()

0.5.0 (2018-11-05)
++++++++++++++++++

* New function: node_api.get_observation()

0.4.0 (2018-11-05)
++++++++++++++++++

* create_observation() now raises exceptions in case of errors.

0.3.0 (2018-11-05)
++++++++++++++++++

* update_observation() now raises exceptions in case of errors.

0.2.0 (2018-10-31)
++++++++++++++++++

* Better infrastructure (type annotations, documentation, ...)
* Dropped support for Python 2.
* New function: update_observation()
* rest_api.AuthenticationError is now exceptions.AuthenticationError


0.1.0 (2018-10-10)
++++++++++++++++++

* First release on PyPI.
