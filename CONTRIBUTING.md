# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

## Installation
To set up for local development (requires [poetry](python-poetry.org)):
```bash
$ git clone https://github.com/niconoe/pyinaturalist.git
$ cd pyinaturalist
$ poetry install -v -E docs
$ # Optional but recommended:
$ pre-commit install --config .github/pre-commit.yml
```

## Contribution Guidelines

### Documentation
We use [Sphinx](http://www.sphinx-doc.org), and the references page is automatically
generated thanks to `sphinx.ext.autodoc` and `sphinx_autodoc_typehints` extensions. All
functions / methods / classes should have proper docstrings.

To build the docs locally:
```bash
$ make -C docs html
```

To preview:
```bash
# MacOS:
$ open docs/_build/index.html
# Linux:
$ xdg-open docs/_build/index.html
```

Documentation is automatically built by ReadTheDocs whenever code is merged into `main`:
* [Stable version (tags only))](https://pyinaturalist.readthedocs.io/en/stable/)
* [Development version (all other commits)](https://pyinaturalist.readthedocs.io/en/latest/)

For any new or changed behavior, add a brief high-level summary to `HISTORY.md`.
This isn't needed for internal changes (tests, other docs, refactoring, etc.).

### Tests
We use the [pytest](https://docs.pytest.org/en/latest/) framework for unit testing.
Just run the `pytest` command to run locally.

We also use [tox](https://tox.readthedocs.io/en/latest/) to test multiple python versions.
Use the `tox` command to run locally. This is also run by GitHub Actions on all pull requests.

### Type Annotations
All parameters and return values should have type annotations, which will be checked by `mypy` and
will show up in the documentation.

### Formatting, Linting, Type Checking, Etc.
Code checking and formatting tools used include:
* [black](https://github.com/psf/black)
* [isort](https://pycqa.github.io/isort/)
* [flake8](https://flake8.pycqa.org/en/latest/)
* [mypy](https://mypy.readthedocs.io/en/stable/getting_started.html)

All of these will be run by GitHub Actions on pull requests.

#### Pre-Commit Hooks
Optionally, there is included config to easily set these up to run as a
[pre-commit hook](https://github.com/pre-commit/pre-commit):
```bash
pre-commit install --config .github/pre-commit.yml
```

This can save you some time in that it will show you errors immediately rather than waiting for CI
jobs to complete. You can disable these hooks at any time with:
```bash
pre-commit uninstall
```

### Pull Requests
Here are some general guidelines for submitting a pull request:

- If the changes are trivial, just briefly explain the changes in the PR description.
- Otherwise, please submit an issue describing the proposed change prior to submitting a PR.
- Make sure the code is tested, annotated and documented as described above.
- Submit the PR to be merged into the `main` branch.

### Releases
For maintainers:

Releases are based on git tags. GitHub Actions will build and deploy packages to PyPi on tagged commits
on the `main` branch. Release steps:

- Update the version in `pyinaturalist/__init__.py`
- Update the release notes in `HISTORY.md`
- Merge changes into the `main` branch
- Push a new tag, e.g.: `git tag v0.1 && git push origin --tags`
- This will trigger a deployment. Verify that this completes successfully and that the new version
  can be installed from pypi with `pip install`


## Types of Contributions
You can contribute in many ways:

### Report Bugs
Report bugs at https://github.com/niconoe/pyinaturalist/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs
Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

### Implement Features
Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

### Write Documentation
pyinaturalist could always use more documentation, whether as part of the
official pyinaturalist docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback
The best way to send feedback is to [create an issue](https://github.com/niconoe/pyinaturalist/issues/new/choose)

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)
