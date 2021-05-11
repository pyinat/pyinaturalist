#!/usr/bin/env python
from itertools import chain
from setuptools import find_packages, setup

from pyinaturalist import __version__

# These package categories allow tox and build environments to install only what they need
extras_require = {
    # Packages used for CI jobs
    'build': ['coveralls', 'twine', 'wheel'],
    # Packages used for documentation builds
    'docs': [
        'm2r2',
        'nbsphinx',
        'prompt_toolkit',
        'Sphinx~=3.5.3',
        'sphinx-autodoc-typehints',
        'sphinx-automodapi',
        'sphinx-copybutton',
        'sphinx-rtd-theme~=0.5.2',
        'sphinxcontrib-apidoc',
    ],
    # Packages used for testing both locally and in CI jobs
    'test': [
        'black==20.8b1',
        'flake8',
        'isort',
        'mypy',
        'pre-commit',
        'pytest>=5.0',
        'pytest-cov',
        'pytest-xdist',
        'requests-mock>=1.7',
        'tox>=3.15',
    ],
    # Packages used only for local debugging
    'debug': ['ipython', 'ipdb', 'prance[osv]', 'rich'],
}
# All development/testing packages combined
extras_require['dev'] = list(chain.from_iterable(extras_require.values()))


setup(
    name='pyinaturalist',
    version=__version__,
    author='Nicolas Noé',
    author_email='nicolas@niconoe.eu',
    url='https://github.com/niconoe/pyinaturalist',
    packages=find_packages(exclude=['examples', 'test']),
    include_package_data=True,
    install_requires=[
        'keyring>=22.3',
        'pyrate-limiter>=2.3.3',
        'python-dateutil>=2.0',
        'python-forge',
        'requests>=2.20',
    ],
    python_requires='>=3.6',
    extras_require=extras_require,
    zip_safe=False,
)
