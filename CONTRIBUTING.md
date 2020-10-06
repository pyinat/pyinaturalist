# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

## Contribution Guidelines

### Documentation

We use [Sphinx](http://www.sphinx-doc.org/en/master/), and the references page is automatically
generated thanks to `sphinx.ext.autodoc` and `sphinx_autodoc_typehints` extensions. All
functions / methods / classes should have proper docstrings.

To build the docs locally:
```bash
$ tox -e docs
```

To preview:
```bash
# MacOS:
$ open docs/_build/index.html
# Linux:
$ xdg-open docs/_build/index.html
```

[Hosted documentation](https://pyinaturalist.readthedocs.io/) is automatically updated when code
gets pushed to the `master` branch.

For any new or changed behavior, add a brief high-level summary to `HISTORY.md`.
This isn't needed for internal changes (tests, other docs, refactoring, etc.).

### Tests

We use the [pytest](https://docs.pytest.org/en/latest/) framework for unit testing.

Just run the `pytest` command to run locally.

We also use [tox](https://tox.readthedocs.io/en/latest/) to test multiple python versions, as well as test coverage, style, and type checks:

Use the `tox` command to run locally. This is also run by Travis CI on all pull requests.

### Type Annotations

All functions / methods should have parameters and return value type annotations.
Those type annotations are checked by MyPy (`tox -e mypy`) and will appear in the documentation.

### Pull Requests
Here are some general guidelines for submitting a pull request:

- If the changes are trivial, just briefly explain the changes in the PR description.
- Otherwise, please submit an issue describing the proposed change prior to submitting a PR.
- Make sure the code is tested, annotated and documented as described above.
- Submit the PR to be merged into the `dev` branch.

### Releases
For maintainers:

Releases are based on git tags. Travis CI will build and deploy packages to PyPi on tagged commits
on the `master` branch. Release steps:

- Update the version in `pyinaturalist/__init__.py`
- Update the release notes in `HISTORY.md`
- Merge changes into the `master` branch
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
The best way to send feedback is to file an issue at https://github.com/niconoe/pyinaturalist/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)
