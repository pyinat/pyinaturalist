#!/usr/bin/env python
from sys import version_info
from setuptools import setup, find_packages
from pyinaturalist import __version__

# Only install the typing backport if we're on python < 3.5
backports = ["typing>=3.7.4"] if version_info < (3, 5) else []


setup(
    name="pyinaturalist",
    version=__version__,
    author="Nicolas Noé",
    author_email="nicolas@niconoe.eu",
    url="https://github.com/niconoe/pyinaturalist",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil>=2.0", "requests>=2.21.0"] + backports,
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
            "pytest-cov",
            "requests-mock>=1.7",
            "Sphinx",
            "sphinx-autodoc-typehints",
            "sphinx-rtd-theme",
            "tox",
        ],
        # Additional packages used only within CI jobs
        "build": ["coveralls", "tox-travis"],
    },
    zip_safe=False,
)
