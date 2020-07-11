#!/usr/bin/env python
from itertools import chain
from setuptools import setup, find_packages
from pyinaturalist import __version__

# These package categories allow tox and build environments to install only what they need
extras_require = {
    # Packages used for CI jobs
    "build": ["coveralls", "tox-travis"],
    # Packages used for documentation builds
    "docs": ["Sphinx>=3.0", "sphinx-rtd-theme", "sphinx-autodoc-typehints", "sphinxcontrib-apidoc"],
    # Packages used for testing both locally and in CI jobs
    "test": [
        "black",
        "flake8",
        "mypy",
        "pytest>=5.0",
        "pytest-cov",
        "requests-mock>=1.7",
        "tox>=3.15",
    ],
}
# All development/testing packages combined
extras_require["dev"] = list(chain.from_iterable(extras_require.values()))


setup(
    name="pyinaturalist",
    version=__version__,
    author="Nicolas Noé",
    author_email="nicolas@niconoe.eu",
    url="https://github.com/niconoe/pyinaturalist",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil>=2.0", "requests>=2.21.0"],
    extras_require=extras_require,
    zip_safe=False,
)
