General Usage
=============
Following is some general usage information that applies to most or all pyinaturalist functions.

Authentication
--------------
See :py:func:`.get_access_token` for pyinaturalist usage info and examples.

For any endpoints that create, update, or delete data, you will need to authenticate using credentials for an
`iNaturalist Application <https://www.inaturalist.org/oauth/applications/new>`_. See `iNaturalist documentation <https://www.inaturalist.org/pages/api+reference#au>`_
for more details on authentication,

.. note::

    Read-only requests generally don't require authentication; however, if you want to access
    private data visible only to your user (for example, obscured or private coordinates),
    you will need to use an access token.


Dry-run mode
------------
While developing & testing an application that uses an API or other remote service, it can be
useful to temporarily mock out HTTP requests, especially requests that add, modify, or delete
real data. Pyinaturalist has some settings to make this easier.

Dry-run all requests
^^^^^^^^^^^^^^^^^^^^
To enable dry-run mode, set the ``DRY_RUN_ENABLED`` variable. When set, requests will not be sent
but will be logged instead:

.. code-block:: python

    >>> import logging
    >>> import pyinaturalist

    # Enable at least INFO-level logging
    >>> logging.basicConfig(level='INFO')

    >>> pyinaturalist.DRY_RUN_ENABLED = True
    >>> get_taxa(q='warbler', locale=1)
    {'results': [], 'total_results': 0}
    INFO:pyinaturalist.api_requests:Request: GET, https://api.inaturalist.org/v1/taxa,
        params={'q': 'warbler', 'locale': 1},
        headers={'Accept': 'application/json', 'User-Agent': 'Pyinaturalist/0.9.1'}

Or, if you are running your application in a command-line environment, you can set this as an
environment variable instead (case-insensitive):

.. code-block:: bash

    $ export DRY_RUN_ENABLED=true
    $ python my_script.py

Dry-run only write requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you would like to run ``GET`` requests but mock out any requests that modify data
(``POST``, ``PUT``, ``DELETE``, etc.), you can use the ``DRY_RUN_WRITE_ONLY`` variable
instead:

.. code-block:: python

    >>> pyinaturalist.DRY_RUN_WRITE_ONLY = True

    # Also works as an environment variable
    >>> import os
    >>> os.environ["DRY_RUN_WRITE_ONLY"] = 'True'


User Agent
----------
While not mandatory, it is considered good practice in the iNaturalist community to set a custom `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ header to your API
calls. That allows iNaturalist to identify "who's doing what" with their APIs, and maybe contact you back in case they want to start
a discussion about how you use them.

It is recommended to set this user-agent field to either something that identifies the project (``MyCoolAndroidApp/2.0``) or its
contact person (``Jane Doe, iNat user XXXXXX, jane@doe.net``).

Pyinaturalist therefore provides a couple of features to make that easy:

.. code-block:: python

    import pyinaturalist
    from pyinaturalist.node_api import get_observation

    pyinaturalist.user_agent = "MyCoolAndroidApp/2.0 (using Pyinaturalist)"

    # From now on, all API calls will use this user-agent.

    t = get_access_token('username', 'password', 'app_id', 'app_secret')
    do_something_else()
    get_observation(observation_id=1234)
    ...

In the rare cases where you want to use multiple user agents in your script, you can configure it per call:

.. code-block:: python

    get_observation(observation_id=16227955, user_agent='AnotherUserAgent')

All functions that communicate with the API accept the `user_agent` optional parameter. If you don't configure the user agent, `Pyinaturalist/<VERSION>` will be used.

