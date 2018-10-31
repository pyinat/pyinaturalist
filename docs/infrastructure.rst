Infrastructure
==============

Documentation
-------------

We use `Sphinx <http://www.sphinx-doc.org/en/master/>`_, and the references page is automatically generated thanks to
``sphinx.ext.autodoc`` and ``sphinx_autodoc_typehints`` extensions. All functions / methods / classes should have a
proper docstring.

To build the doc locally::

    $ tox -e docs

Hosted documentation (https://pyinaturalist.readthedocs.io/) is automatically updated when code gets pushed to GitHub.

Testing
-------

We use the `pytest framework <https://docs.pytest.org/en/latest/>`_.

To run locally::

    $ pytest

It is however always good to run ``tox`` frequently, to run the tests against multiple Python versions, as well as some
style and type annotations checks::

    $ tox

Type annotations
----------------

All functions / methods should have parameters and return value type annotations. Those type annotations are checked by
MyPy (``tox -e mypy``) and will appear in the documentation.

PyPI
----

Release checklist:

- Make sure the code is tested, annotated and documented.
- Update HISTORY.rst and setup.py
- Push a vX.Y.Z tag to GitHub
- Use twine to upload the package to PyPI


