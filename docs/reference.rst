Reference
=========

iNaturalist actually provides two APIs:

- the `REST API <https://www.inaturalist.org/pages/api+reference>`_ that they also use internally: it is very complete
  and provides read/write access, but is rather slow and sometimes inconsistent.
- the `Node-based API <https://api.inaturalist.org/v1/docs/>`_ allows searching and returning core data, is faster and
  provides more consistent returned results than the REST API, but has less features.

Pyinaturalist provides functions to use both of those APIs.

REST API
--------

.. automodule:: pyinaturalist.rest_api
    :members:
    :show-inheritance:

Node-based API
--------------

.. automodule:: pyinaturalist.node_api
    :members:
    :show-inheritance:

Exceptions
----------

.. automodule:: pyinaturalist.exceptions
    :members:
    :show-inheritance:

