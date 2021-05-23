.. _endpoints:

Endpoint Summary
================
Below is a list of all iNaturalist API endpoints and their corresponding pyinaturalist functions.
Note that some endpoints have more than one function associated with them.


Pyinaturalist functions
----------------------------------------

API v1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodsumm:: pyinaturalist.v1
    :functions-only:
    :nosignatures:

API v0
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. automodsumm:: pyinaturalist.v0
    :functions-only:
    :nosignatures:


All iNaturalist endpoints
----------------------------------------
.. Writing the table in markdown because markdown table syntax is much more sane than rst

.. note::

    The two iNaturalist APIs expose a combined total of 102 endpoints. Some of these are generally
    useful and could potentially be added to pyinaturalist, but many others are primarily for
    internal use by the iNaturalist web application and mobile apps, and are unlikely to be added
    unless there are specific use cases for them.

.. mdinclude:: endpoints_table.md
    :start-line: 1
