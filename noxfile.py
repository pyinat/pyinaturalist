"""Notes:
* 'test' command: nox will create new virtualenvs per python version
* 'lint' command: tools and environments are managed by pre-commit
* All other commands: will use the project virtualenv managed by uv
"""

from os import getenv
from os.path import join
from shutil import rmtree

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = ['lint', 'cov']

LIVE_DOCS_PORT = 8181
LIVE_DOCS_IGNORE = ['*.csv', '*.ipynb', '*.pyc', '*.tmp', '**/modules/*']
LIVE_DOCS_WATCH = ['pyinaturalist', 'examples']
DEFAULT_COVERAGE_FORMATS = ['html', 'term']
DOC_BUILD_DIR = join('docs', '_build', 'html')
CLEAN_DIRS = [
    'dist',
    'build',
    join('docs', '_build'),
    join('docs', 'models'),
    join('docs', 'modules'),
]


@nox.session(python=['3.8', '3.9', '3.10', '3.11', '3.12', '3.13'])
def test(session):
    """Run tests for a specific python version"""
    test_paths = session.posargs or ['test']
    session.install('.', 'filelock', 'pytest', 'pytest-sugar', 'pytest-xdist', 'requests-mock')
    session.run('pytest', '-n', 'auto', *test_paths)


@nox.session(python=False)
def clean(session):
    """Clean up temporary build + documentation files"""
    for dir in CLEAN_DIRS:
        print(f'Removing {dir}')
        rmtree(dir, ignore_errors=True)


@nox.session(python=False, name='cov')
def coverage(session):
    """Run tests and generate coverage report"""
    cmd = ['uv', 'run', 'pytest', '--numprocesses=auto', '--cov']

    # Add coverage formats
    cov_formats = session.posargs or DEFAULT_COVERAGE_FORMATS
    cmd += [f'--cov-report={f}' for f in cov_formats]

    # Add verbose flag, if set by environment
    if getenv('PYTEST_VERBOSE'):
        cmd += ['--verbose']
    session.run(*cmd)


@nox.session(python=False)
def docs(session):
    """Build Sphinx documentation"""
    session.run('uv', 'run', 'sphinx-build', 'docs', DOC_BUILD_DIR, '-j', 'auto')


@nox.session(python=False)
def livedocs(session):
    """Auto-build docs with live reload in browser.
    Add `-- open` to also open the browser after starting.
    """
    cmd = ['uv', 'run', 'sphinx-autobuild', 'docs', DOC_BUILD_DIR]
    cmd += ['-a']
    cmd += ['--port', str(LIVE_DOCS_PORT), '-j', 'auto']
    for pattern in LIVE_DOCS_WATCH:
        cmd += ['--watch', pattern]
    for pattern in LIVE_DOCS_IGNORE:
        cmd += ['--ignore', pattern]
    if session.posargs == ['open']:
        cmd.append('--open-browser')

    clean(session)
    session.run(*cmd)


@nox.session(python=False)
def lint(session):
    """Run linters and code formatters via pre-commit"""
    session.run('pre-commit', 'run', '--all-files')
