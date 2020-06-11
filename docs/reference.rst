Reference
=========

iNaturalist actually provides two APIs:

- the `REST API <https://www.inaturalist.org/pages/api+reference>`_ that they also use internally: it is very complete
  and provides read/write access, but is rather slow and sometimes inconsistent.
- the `Node-based API <https://api.inaturalist.org/v1/docs/>`_ allows searching and returning core data, is faster and
  provides more consistent returned results than the REST API, but has less features.

Pyinaturalist provides functions to use both of those APIs.

.. note::

    While not mandatory, it is considered good practice in the iNaturalist community to set a custom `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ header to your API
    calls. That allows iNaturalist to identify "who's doing what" with their APIs, and maybe contact you back in case they want to start
    a discussion about how you use them.

    It is recommended to set this user-agent field to either something that identifies the project (MyCoolAndroidApp/2.0) or its
    contact person (Jane Doe, iNat user XXXXXX, jane@doe.net).

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

    (All functions that communicate with the API accept the `user_agent` optional parameter).

    If you don't configure the user agent, `Pyinaturalist/<VERSION>` will be used.

