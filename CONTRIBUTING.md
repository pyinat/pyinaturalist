# Contributing Guide
Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

## Installation
To set up for local development (requires [poetry](https://python-poetry.org)):
```bash
$ git clone https://github.com/niconoe/pyinaturalist.git
$ cd pyinaturalist
$ poetry install -v -E docs
```

## Contribution Guidelines

### Documentation
For PRs, please include docstrings for all functions and classes.

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

Project documentation is generated using [Sphinx](https://www.sphinx-doc.org),
[MyST](https://myst-parser.readthedocs.io), and several Sphinx extensions and custom templates.
See [conf.py](https://github.com/niconoe/pyinaturalist/blob/main/docs/conf.py) for more details.

Documentation is automatically built by ReadTheDocs whenever code is merged into `main`:
* [Stable version (tags only))](https://pyinaturalist.readthedocs.io/en/stable/)
* [Development version (all other commits)](https://pyinaturalist.readthedocs.io/en/latest/)

For any new or changed behavior, add a brief high-level summary to `HISTORY.md`.
This isn't needed for internal changes (tests, other docs, refactoring, etc.).

### Tests
We use the [pytest](https://docs.pytest.org/en/latest/) framework for unit testing.
Just run the `pytest` command to run locally.

For PRs, GitHub Actions will also run tests for all supported python versions.
You can use [tox](https://tox.readthedocs.io/en/latest/) to test these versions locally.

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
