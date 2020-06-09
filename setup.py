#!/usr/bin/env python
from setuptools import setup, find_packages
from pyinaturalist import __version__


setup(
    name="pyinaturalist",
    version=__version__,
    author="Nicolas Noé",
    author_email="nicolas@niconoe.eu",
    url="https://github.com/niconoe/pyinaturalist",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["python-dateutil>=2.0", "requests>=2.21.0", "typing>=3.7.4"],
    extras_require={
        "dev": [
            "black",
            "coveralls",
            "flake8",
            "mypy",
            "pytest",
            "pytest-cov",
            "requests-mock>=1.7",
            "Sphinx",
            "sphinx-autodoc-typehints",
            "sphinx-rtd-theme",
            "tox",
            "twine",
        ]
    },
    zip_safe=False,
)
