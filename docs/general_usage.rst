General Usage
=============
This page contains usage information that applies to most or all pyinaturalist functions.

Installation
------------
Install the latest stable version with pip::

    pip install pyinaturalist

Or with Conda, if you prefer::

    conda install -c conda-forge pyinaturalist

If you would like to use the latest development (pre-release) version::

    pip install --pre pyinaturalist

See :ref:`contributing` for details on setup for local development.


Pagination
----------
Most endpoints support pagination, using the parameters:
    * ``page``: Page number to get
    * ``per_page``: Number of results to get per page
    * ``count_only=True``: This is just a shortcut for ``per_page=0``, which will return only the
      total number of results, not the results themselves.

The default and maximum ``per_page`` values vary by endpoint, but it's 200 for most endpoints.

To get all pages of results and combine them into a single response, use ``page='all'``.
Note that this replaces the ``get_all_*()`` functions from pyinaturalist<=0.12.

.. _auth:

Authentication
--------------
For any endpoints that create, update, or delete data, you will need to authenticate using credentials for an
`iNaturalist Application <https://www.inaturalist.org/oauth/applications/new>`_.

See `iNaturalist documentation <https://www.inaturalist.org/pages/api+reference#auth>`_
for more details on authentication, and see :py:func:`.get_access_token` for pyinaturalist usage info and examples.

.. note::

    Read-only requests generally don't require authentication; however, if you want to access
    private data visible only to your user (for example, obscured or private coordinates),
    you will need to use an access token.

In addition to :py:func:`.get_access_token` arguments, there are some other options for
providing credentials:

Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You may provide credentials via environment variables instead of arguments. The
environment variable names are the keyword arguments in uppercase, prefixed with ``INAT_``:

* ``INAT_USERNAME``
* ``INAT_PASSWORD``
* ``INAT_APP_ID``
* ``INAT_APP_SECRET``

**Examples:**

.. admonition:: Set environment variables in python:
    :class: toggle

    >>> import os
    >>> os.environ['INAT_USERNAME'] = 'my_username'
    >>> os.environ['INAT_PASSWORD'] = 'my_password'
    >>> os.environ['INAT_APP_ID'] = '33f27dc63bdf27f4ca6cd95dd9dcd5df'
    >>> os.environ['INAT_APP_SECRET'] = 'bbce628be722bfe2abd5fc566ba83de4'

.. admonition:: Set environment variables in a POSIX shell (bash, etc.):
    :class: toggle

    .. code-block:: bash

        export INAT_USERNAME="my_username"
        export INAT_PASSWORD="my_password"
        export INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
        export INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

.. admonition:: Set environment variables in a Windows shell:
    :class: toggle

    .. code-block:: bat

        set INAT_USERNAME="my_username"
        set INAT_PASSWORD="my_password"
        set INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
        set INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

.. admonition:: Set environment variables in PowerShell:
    :class: toggle

    .. code-block:: powershell

        $Env:INAT_USERNAME="my_username"
        $Env:INAT_PASSWORD="my_password"
        $Env:INAT_APP_ID="33f27dc63bdf27f4ca6cd95dd9dcd5df"
        $Env:INAT_APP_SECRET="bbce628be722bfe2abd5fc566ba83de4"

Note that in any shell, these environment variables will only be set for your current shell
session. I.e., you can't set them in one terminal and then access them in another.

Keyring Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To handle your credentials more securely, you can store them in your system keyring.
You could manually store and retrieve them with a utility like
`secret-tool <https://manpages.ubuntu.com/manpages/xenial/man1/secret-tool.1.html>`_
and place them in environment variables as described above, but there is a much simpler option.

Direct keyring integration is provided via `python keyring <https://github.com/jaraco/keyring>`_. Most common keyring bakcends are supported, including:

* macOS `Keychain
  <https://en.wikipedia.org/wiki/Keychain_%28software%29>`_
* Freedesktop `Secret Service
  <http://standards.freedesktop.org/secret-service/>`_
* KDE `KWallet <https://en.wikipedia.org/wiki/KWallet>`_
* `Windows Credential Locker
  <https://docs.microsoft.com/en-us/windows/uwp/security/credential-locker>`_

To store your credentials in the keyring, run :py:func:`.set_keyring_credentials`:

    >>> from pyinaturalist.auth import set_keyring_credentials
    >>> set_keyring_credentials(
    >>>     username='my_username',
    >>>     password='my_password',
    >>>     app_id='33f27dc63bdf27f4ca6cd95dd9dcd5df',
    >>>     app_secret='bbce628be722bfe2abd5fc566ba83de4',
    >>> )

Afterward, you can call :py:func:`.get_access_token` without any arguments, and your credentials
will be retrieved from the keyring. You do not need to run :py:func:`.set_keyring_credentials`
again unless you change your iNaturalist password.

Password Manager Integration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Keyring integration can be taken a step further by managing your keyring with a password
manager. This has the advantage of keeping your credentials in one place that can be synced
across multiple machines. `KeePassXC <https://keepassxc.org/>`_ offers this feature for
macOS and Linux systems. See this guide for setup info:
`KeepassXC and secret service, a small walk-through
<https://avaldes.co/2020/01/28/secret-service-keepassxc.html>`_.

.. figure:: images/password_manager_keying.png
   :alt: map to buried treasure

   Credentials storage with keyring + KeePassXC


Dry-run mode
------------
While developing and testing, it can be useful to temporarily mock out HTTP requests, especially
requests that add, modify, or delete real data. Pyinaturalist has some settings to make this easier.

Dry-run all requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To enable dry-run mode, set the ``DRY_RUN_ENABLED`` variable. When set, requests will not be sent
but will be logged instead:

    >>> import logging
    >>> import pyinaturalist
    >>>
    >>> # Enable at least INFO-level logging
    >>> logging.basicConfig(level='INFO')
    >>>
    >>> pyinaturalist.DRY_RUN_ENABLED = True
    >>> get_taxa(q='warbler', locale=1)
    {'results': [], 'total_results': 0}
    INFO:pyinaturalist.api_requests:Request: GET, https://api.inaturalist.org/v1/taxa,
        params={'q': 'warbler', 'locale': 1},
        headers={'Accept': 'application/json', 'User-Agent': 'Pyinaturalist/0.9.1'}

You can also set this as an environment variable (case-insensitive):

.. code-block:: bash

    $ export DRY_RUN_ENABLED=true
    $ python my_script.py

Dry-run only write requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you would like to send real ``GET`` requests but mock out any requests that modify data
(``POST``, ``PUT``, ``DELETE``, etc.), you can use the ``DRY_RUN_WRITE_ONLY`` variable
instead:

    >>> pyinaturalist.DRY_RUN_WRITE_ONLY = True
    >>> # Also works as an environment variable
    >>> import os
    >>> os.environ["DRY_RUN_WRITE_ONLY"] = 'True'


User Agent
----------
While not mandatory, it's good practice to include a `user-agent <https://en.wikipedia.org/wiki/User_agent>`_ in
your API calls. This field can be either something that identifies the project or its contact person.

You can either set this globally:

    >>> import pyinaturalist
    >>> from pyinaturalist.node_api import get_observation
    >>>
    >>> pyinaturalist.user_agent = "MyCoolAndroidApp/2.0 (using Pyinaturalist)"
    >>> # From now on, all API calls will use this user-agent.


To set this for individual requests, all API functions accept an optional ``user_agent`` parameter:

    >>> get_observation(observation_id=16227955, user_agent='Jane Doe <jane.doe@gmail.com>')

If not configured, ``Pyinaturalist/<VERSION>`` will be used.


API Recommended Practices
-------------------------
See `API Recommended Practices <https://www.inaturalist.org/pages/api+recommended+practices>`_
on iNaturalist for more general usage information and notes.
