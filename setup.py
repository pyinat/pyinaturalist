#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

readme = open("README.rst").read()

history = open("HISTORY.rst").read().replace(".. :changelog:", "")

setup(
    name="pyinaturalist",
    version="0.9.0",
    description="Python client for the iNaturalist APIs",
    long_description=readme + "\n\n" + history,
    author="Nicolas Noé",
    author_email="nicolas@niconoe.eu",
    url="https://github.com/niconoe/pyinaturalist",
    packages=["pyinaturalist"],
    package_dir={"pyinaturalist": "pyinaturalist"},
    include_package_data=True,
    install_requires=["requests>=2.21.0", "typing>=3.7.4"],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
            "requests-mock>=1.7",
            "Sphinx",
            "sphinx-autodoc-typehints",
            "sphinx-rtd-theme",
            "tox",
            "twine"
        ]
    },
    license="MIT",
    zip_safe=False,
    keywords="pyinaturalist",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
