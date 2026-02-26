# Contributing Guide
If you use this project and want to help improve it, contributions are very welcome!

## Installation
To set up for local development (requires [uv](https://docs.astral.sh/uv)):
```bash
$ git clone https://github.com/pyinat/pyinaturalist.git
$ cd pyinaturalist
$ uv sync --all-extras --all-groups
```

## Contribution Guidelines

### AI Policy
AI-assisted contributions are acceptable if:
* Contents are fully **reviewed, tested, and understood by a human**
* Any user-facing documentation is human-written (excluding minor edits/docstring boilerplate)
* You are a user of this project, or of iNaturalist, or are otherwise involved in biodiversity data
  and citized science

The general principle is that low-effort, fully automated contributions add a maintenance burden for
me (a limited and squishy mortal being) that is out of proportion with the utility these PRs provide,
especially if they are submitted solely for contribution stats.

### Pull Requests
Here are some general guidelines for submitting a pull request:
- Use the PR template
- If the changes are trivial, just submit a PR and briefly explain the changes in the description.
- Otherwise, please submit an issue describing the proposed change prior to submitting a PR.
- Make sure the code is tested, documented, and type-annotated (as described in sections below).
- Submit the PR to be merged into the `main` branch.

### Tests
To run all tests and linting:
```sh
uv run nox
```

#### Testing supported python versions
For PRs, GitHub Actions will run these tests for each supported python version.

You can use [nox](https://nox.thea.codes) to do this locally, if needed:
```bash
uv run nox -e test
```

Or to run tests for a specific python version:
```bash
uv run nox -e test-3.10
```

See `nox --list` for a full list of available commands.

### Documentation
For PRs, please include docstrings for all functions and classes.

To build the docs locally:
```bash
$ uv run nox -e docs
```

To preview:
```bash
# MacOS:
$ open docs/_build/html/index.html
# Linux:
$ xdg-open docs/_build/html/index.html
```

You can also use [sphinx-autobuild](https://github.com/executablebooks/sphinx-autobuild) to rebuild the docs and live reload in the browser whenever doc contents change:
```bash
$ uv run nox -e livedocs
```

Project documentation is generated using [Sphinx](https://www.sphinx-doc.org),
[MyST](https://myst-parser.readthedocs.io), and several Sphinx extensions and custom templates.
See [conf.py](https://github.com/pyinat/pyinaturalist/blob/main/docs/conf.py) for more details.

Documentation is automatically built by ReadTheDocs whenever code is merged into `main`:
* [Stable version (tags only))](https://pyinaturalist.readthedocs.io/en/stable/)
* [Development version (all other commits)](https://pyinaturalist.readthedocs.io/en/latest/)

For any new or changed behavior, add a brief high-level summary to `HISTORY.md`.
This isn't needed for internal changes (tests, other docs, refactoring, etc.).

### Type Annotations
All parameters and return values should have type annotations, which will be checked by `mypy` and
will show up in the documentation.

### Linting & Formatting
Code checking and formatting tools used include:
* [ruff (linter)](https://docs.astral.sh/ruff/linter)
* [ruff (formatter)](https://docs.astral.sh/ruff/formatter)
* [mypy](https://mypy.readthedocs.io/en/stable/getting_started.html)

All of these will be run by GitHub Actions on pull requests. You can also run them locally with:
```bash
prek run -a
```

#### Pre-Commit Hooks
Optionally, you can use [prek](https://github.com/j178/prek) (or [pre-commit](https://github.com/pre-commit/pre-commit), if you prefer) to automatically
run all of these checks before a commit is made:
```bash
prek install
```

This can save you some time in that it will show you errors immediately rather than waiting for CI
jobs to complete, or if you forget to manually run the checks before committing.

You can disable these hooks at any time with:
```bash
prek uninstall
```

### Releases
Notes for maintainers on publishing new releases:

Releases are based on git tags. GitHub Actions will build and deploy packages to PyPi on tagged commits
on the `main` branch. Release steps:
- Update the version in both `pyproject.toml` and `pyinaturalist/__init__.py`
- Update the release notes in `HISTORY.md`
- Push a new tag, e.g.: `git tag v0.1.0 && git push --tags`
- This will trigger a deployment. Verify that this completes successfully and that the new version
  can be installed from PyPI with `pip install pyinaturalist`.
- Verify that the docs are built and published to [Read The Docs](https://pyinaturalist.readthedocs.io).
- A PR for a new Conda release will be created by a bot on the [pyinaturalist-feedstock](https://github.com/conda-forge/pyinaturalist-feedstock/)
  repo. It may take a couple hours after PyPI deployment for this to happen. Typically this will be
  auto-merged and built without any manual action required. Just verify that this completes successfully
  and that the new version can be installed from conda-forge with `conda install -c conda-forge pyinaturalist`.
  - If new dependencies have been added, then those must also be added to the [conda recipe](https://github.com/conda-forge/pyinaturalist-feedstock/blob/master/recipe/meta.yaml).
- A Docker build will be triggered for [pyinaturalist-notebook](https://github.com/JWCook/pyinaturalist-notebook).
  Verify that this successfully gets deployed to Docker Hub.
