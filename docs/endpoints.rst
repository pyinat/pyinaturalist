.. _endpoints:

Endpoint Summary
================
Below is a list of all iNaturalist API endpoints and their corresponding pyinaturalist functions.
Note that some endpoints have more than one function associated with them.


Pyinaturalist functions
----------------------------------------

v1 API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodsumm:: pyinaturalist.v1
    :functions-only:
    :nosignatures:
    :skip: get_v1

v0 API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodsumm:: pyinaturalist.v0
    :functions-only:
    :nosignatures:


All iNaturalist endpoints
----------------------------------------
.. Writing the table in markdown because markdown table syntax is much more sane than rst

.. note::

    The two iNaturalist APIs expose a combined total of 104+ endpoints. Some of these are generally
    useful and could potentially be added to pyinaturalist, but many others are primarily for
    internal use by iNaturalist.org and its mobile apps, and are unlikely to be added unless
    specifically requested.

.. mdinclude:: endpoints_table.md
    :start-line: 1
