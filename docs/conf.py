"""Summary of documentation components:

* ``forge`` is used to define and reuse documentation for API request parameters
* ``apidoc`` is used to generate rst sources for **modules**
* ``autosummary`` is used to generate rst sources for **packages and summaries**
* ``automodapi`` + ``pyinaturalist.api_docs.model_docs`` are used to generate model
  documentation based on ``attrs`` fields + metadata
* ``intersphinx`` is used to insert links to other projects' docs
* Jinja templates provide some additional customization:
    * Show a class summary for ``pyinaturalist.models`` package
    * Show a function summary for ``pyinaturalist.v*`` packages
    * Show a function summary for all modules except ``pyinaturalist.models.*``
* Some Sphinx builder hooks copy some content so it can be accessed relative to ``docs`` dir
* Some CSS adds collapsible drop-down container
* Additional CSS is added to customize function-level docs
* A version dropdown (to switch to docs for older versions) is added with ``sphinx-material``, and
  versions are listed in ``static/versions.json``

TODO:
* Customization for package-level docs that can be done with module docstrings instead of templates?
* Automatically generate list of versions for version dropdown?
"""
# flake8: noqa: E402
import sys
from os import makedirs, symlink
from os.path import abspath, dirname, exists, join
from shutil import copytree, rmtree


# Avoid a potential circular import in nbsphinx
try:
    import prompt_toolkit  # noqa
except ImportError:
    pass

DOCS_DIR = abspath(dirname(__file__))
MODULE_DOCS_DIR = join(DOCS_DIR, 'modules')
PROJECT_DIR = dirname(DOCS_DIR)
PACKAGE_DIR = join(PROJECT_DIR, 'pyinaturalist')

# Source paths and symlink paths for static content to include
DATA_DIR_SRC = join(PROJECT_DIR, 'test', 'sample_data')
DATA_DIR_SYMLINK = join(DOCS_DIR, 'sample_data')
IMAGE_DIR_SRC = join(DOCS_DIR, 'images')
IMAGE_DIR_SYMLINK = join(DOCS_DIR, 'docs', 'images')
NOTEBOOK_DIR_SRC = join(PROJECT_DIR, 'examples')
NOTEBOOK_DIR_COPY = join(DOCS_DIR, 'examples')

# Add project path so we can import our package
sys.path.insert(0, PROJECT_DIR)
from pyinaturalist import __version__
from pyinaturalist.api_docs import document_models

# General information about the project.
copyright = '2021, Nicolas Noé, Jordan Cook'
exclude_patterns = ['_build', 'modules/pyinaturalist.rst']
html_static_path = ['_static']
master_doc = 'index'
needs_sphinx = '4.0'
project = 'pyinaturalist'
source_suffix = ['.rst', '.md']
templates_path = ['_templates']
version = release = __version__

# Sphinx extension modules
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'sphinx_automodapi.automodapi',
    'sphinx_automodapi.smart_resolver',
    'sphinx_copybutton',
    'sphinx_material',
    'sphinxcontrib.apidoc',
    'm2r2',
    'nbsphinx',
]

nbsphinx_allow_errors = True

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/master/', None),
}

autosectionlabel_prefix_document = True

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Strip prompt text when copying code blocks with copy button
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True

# Move type hint info to function description instead of signature
autodoc_typehints = 'description'
set_type_checking_flag = True

# apidoc settings
apidoc_module_dir = PACKAGE_DIR
apidoc_output_dir = 'modules'
apidoc_excluded_paths = ['api_docs/*', 'models/*', 'node_api.py', 'rest_api.py']
apidoc_extra_args = ['--templatedir=_templates']
apidoc_module_first = True
apidoc_separate_modules = True
apidoc_toc_file = False

# autosummary + automodapi settings
automodapi_inheritance_diagram = False
automodsumm_inherited_members = False
autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False
numpydoc_show_class_members = False

# HTML theme settings
html_theme = 'sphinx_material'
html_show_sphinx = False
html_theme_options = {
    'color_primary': 'blue-grey',
    'color_accent': 'teal',
    'globaltoc_depth': 3,
    'globaltoc_includehidden': False,
    'master_doc': False,
    'nav_title': project,
    'repo_url': 'https://github.com/niconoe/pyinaturalist',
    'repo_name': project,
    'version_dropdown': True,
    'version_json': '_static/versions.json',
}
html_sidebars = {'**': ['logo-text.html', 'globaltoc.html', 'localtoc.html', 'searchbox.html']}
pygments_style = 'friendly'

# TODO If/when dark mode support is added for sphinx-material
# pygments_style = 'material'

# Favicon & sidebar logo
# html_logo = 'logo.jpg'
html_favicon = join('images', 'favicon.ico')


def setup(app):
    """Run some additional steps after the Sphinx builder is initialized.

    In addition to basic things like adding static resources, this allows us to run any custom
    behavior that would otherwise go in the Makefile, so the readthedocs builder will behave the
    same as building the docs manually.

    Reference:
        * https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
        * https://docs.readthedocs.io/en/stable/builds.html
        * https://github.com/sphinx-contrib/apidoc
    """
    app.connect('builder-inited', document_models)
    app.connect('builder-inited', setup_external_files)
    app.connect('builder-inited', patch_automodapi)
    app.add_css_file('style.css')
    app.add_css_file('collapsible_container.css')


def setup_external_files(app):
    """Create symlinks and copies of files outside docs directory so they can be accessed by Sphinx
    directives.
    """
    make_symlink(IMAGE_DIR_SRC, IMAGE_DIR_SYMLINK)
    make_symlink(DATA_DIR_SRC, DATA_DIR_SYMLINK)
    # Unfortunately this can't be symlinked; nbsphinx will insert image links relative to this dir
    rmtree(NOTEBOOK_DIR_COPY, ignore_errors=True)
    copytree(NOTEBOOK_DIR_SRC, NOTEBOOK_DIR_COPY)


def make_symlink(src, dest):
    makedirs(dirname(dest), exist_ok=True)
    if not exists(dest):
        symlink(src, dest)


def patch_automodapi(app):
    """Monkey-patch the automodapi extension to exclude imported members.

    https://github.com/astropy/sphinx-automodapi/blob/master/sphinx_automodapi/automodsumm.py#L135
    """
    from sphinx_automodapi import automodsumm
    from sphinx_automodapi.utils import find_mod_objs

    automodsumm.find_mod_objs = lambda *args: find_mod_objs(args[0], onlylocals=True)
