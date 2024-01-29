(auth)=
# Authentication
For any endpoints that create, update, or delete data, you will need to authenticate using an
access token. There are two main ways to get one: manually via a browser, or programatically, using
your iNaturalist credentials plus separate application credentials. These tokens are typically valid
for 24 hours, after which you will need to get a new one.

You can then pass the access token to any API request function that uses it via the
`access_token` argument. For example:
```py
from pyinaturalist import create_observation

create_observation(
  ...,
  access_token='my_access_token',
)
```

:::{note} Read-only requests generally don't require authentication; however, if you want to access
private data visible only to your user (for example, obscured or private coordinates), you will need
to use an access token.
:::

## Manual Authentication
You can get an access token from a browser by logging in to inaturalist.org and going to
https://www.inaturalist.org/users/api_token.

This has the advantage of not needing to create an iNaturalist application (see section below), but
has the disadvantage of requiring you to manually copy and paste the token.

## Creating an Application
:::{dropdown} Why do I need to create an application?
:icon: info

iNaturalist uses OAuth2, which provides several different methods (or "flows") to access the site.
For example, on the [login page](https://www.inaturalist.org/login), you have the option of logging
in with a username/password, or with an external provider (Google, Facebook, etc.):

```{image} ../images/inat-user-login.png
:alt: Login form
:width: 150
```

Outside of iNaturalist.org, anything else that uses the API to create or modify data is considered
an "application," even if you're just running some scripts on your own computer.

See [iNaturalist documentation](https://www.inaturalist.org/pages/api+reference#auth)
for more details on authentication.
:::

First, go to [New Application](https://www.inaturalist.org/oauth/applications/new) and fill out the
following pieces of information:

* **Name:** Any name you want to come up with. For example, if this is associated with a GitHub repo,
  you can use your repo name.
* **Description:** A brief description of what you'll be using this for. For example,
  *"Data access for my own observations"*.
* **Confidential:** ✔️ This should be checked.
* **URL and Redirect URI:** Just enter the URL to your GitHub repo, if you have one; otherwise any
  placeholder like "<https://www.inaturalist.org>" will work.

```{image} ../images/inat-new-application.png
:alt: New Application form
:width: 300
```

You should then see a screen like this, which will show your new application ID and secret. These will
only be shown once, so save them somewhere secure, preferably in a password manager.
```{image} ../images/inat-new-application-complete.png
:alt: Completed application form
:width: 400
```

## Basic Usage
There are a few different ways you can pass your credentials to iNaturalist. First, you can pass
them as keyword arguments to {py:func}`.get_access_token`:

```python
>>> from pyinaturalist import get_access_token
>>> access_token = get_access_token(
>>>     username='my_inaturalist_username',  # Username you use to login to iNaturalist.org
>>>     password='my_inaturalist_password',  # Password you use to login to iNaturalist.org
>>>     app_id='33f27dc63bdf27f4ca6cd95dd',  # OAuth2 application ID
>>>     app_secret='bbce628be722bfe2abde4',  # OAuth2 application secret
>>> )
```

## Environment Variables
You can also provide credentials via environment variables instead of arguments. The
environment variable names are the keyword arguments in uppercase, prefixed with `INAT_`:

* `INAT_USERNAME`
* `INAT_PASSWORD`
* `INAT_APP_ID`
* `INAT_APP_SECRET`

**Examples:**

::::{tab-set}
:::{tab-item} Python
:sync: python

```python
>>> import os
>>> os.environ['INAT_USERNAME'] = 'my_inaturalist_username'
>>> os.environ['INAT_PASSWORD'] = 'my_inaturalist_password'
>>> os.environ['INAT_APP_ID'] = '33f27dc63bdf27f4ca6cd95df'
>>> os.environ['INAT_APP_SECRET'] = 'bbce628be722bfe283de4'
```
:::
:::{tab-item} Unix (MacOS / Linux)
:sync: unix

```bash
export INAT_USERNAME="my_inaturalist_username"
export INAT_PASSWORD="my_inaturalist_password"
export INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
export INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
:::{tab-item} Windows CMD
:sync: cmd

```bat
set INAT_USERNAME="my_inaturalist_username"
set INAT_PASSWORD="my_inaturalist_password"
set INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
set INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
:::{tab-item} PowerShell
:sync: ps1

```powershell
$Env:INAT_USERNAME="my_inaturalist_username"
$Env:INAT_PASSWORD="my_inaturalist_password"
$Env:INAT_APP_ID="33f27dc63bdf27f4ca6cd95df"
$Env:INAT_APP_SECRET="bbce628be722bfe283de4"
```
:::
::::

Note that in any shell, these environment variables will only be set for your current shell
session. I.e., you can't set them in one terminal and then access them in another.

## Keyring Integration
To handle your credentials more securely, you can store them in your system keyring.
You could manually store and retrieve them with a utility like
[secret-tool](https://manpages.ubuntu.com/manpages/xenial/man1/secret-tool.1.html)
and place them in environment variables as described above, but there is a much simpler option.

Direct keyring integration is provided via [python keyring](https://github.com/jaraco/keyring). Most common keyring bakcends are supported, including:

* macOS [Keychain](https://en.wikipedia.org/wiki/Keychain_%28software%29)
* Freedesktop [Secret Service](http://standards.freedesktop.org/secret-service/)
* KDE [KWallet](https://en.wikipedia.org/wiki/KWallet)
* [Windows Credential Locker](https://docs.microsoft.com/en-us/windows/uwp/security/credential-locker)

To store your credentials in the keyring, run {py:func}`.set_keyring_credentials`:
```python
>>> from pyinaturalist.auth import set_keyring_credentials
>>> set_keyring_credentials(
>>>     username='my_inaturalist_username',
>>>     password='my_inaturalist_password',
>>>     app_id='33f27dc63bdf27f4ca6cd95df',
>>>     app_secret='bbce628be722bfe283de4',
>>> )
```

Afterward, you can call {py:func}`.get_access_token` without any arguments, and your credentials
will be retrieved from the keyring. You do not need to run {py:func}`.set_keyring_credentials`
again unless you change your iNaturalist password.

### Password Manager Integration
Keyring integration can be taken a step further by managing your keyring with a password
manager. This has the advantage of keeping your credentials in one place that can be synced
across multiple machines. [KeePassXC](https://keepassxc.org/) offers this feature for
macOS and Linux systems. See this guide for setup info:
[KeepassXC and secret service, a small walk-through](https://avaldes.co/2020/01/28/secret-service-keepassxc.html).

```{figure} ../images/password_manager_keying.png
Credentials storage with keyring + KeePassXC
```
