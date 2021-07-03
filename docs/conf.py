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
from glob import glob
from os import makedirs, symlink
from os.path import abspath, basename, dirname, exists, join
from shutil import copytree, rmtree

# Avoid a potential circular import in nbsphinx
try:
    import prompt_toolkit  # noqa
except ImportError:
    pass

# Add project path so we can import our package
sys.path.insert(0, '..')
from pyinaturalist import __version__
from pyinaturalist.constants import DOCS_DIR, PROJECT_DIR, EXAMPLES_DIR, SAMPLE_DATA_DIR
from pyinaturalist.api_docs import document_models

# Relevant doc directories used in extension settings
CSS_DIR = join(DOCS_DIR, '_static')
MODULE_DOCS_DIR = 'modules'
PACKAGE_DIR = join(PROJECT_DIR, 'pyinaturalist')

# Symlink paths for static content outside docs directory
DATA_DIR_SYMLINK = join(DOCS_DIR, 'sample_data')
NOTEBOOK_DIR_COPY = join(DOCS_DIR, 'examples')

# General information about the project.
copyright = '2021, Nicolas Noé, Jordan Cook'
exclude_patterns = ['_build', f'{MODULE_DOCS_DIR}/pyinaturalist.rst']
html_static_path = ['_static']
master_doc = 'index'
needs_sphinx = '4.0'
project = 'pyinaturalist'
source_suffix = ['.rst', '.md']
templates_path = ['_templates']
version = release = __version__

# Sphinx extensions
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
    'myst_parser',
    'nbsphinx',
]

# MyST extensions
myst_enable_extensions = [
    "colon_fence",
    # "deflist",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    # "substitution",
]

nbsphinx_allow_errors = True

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ('https://requests.readthedocs.io/en/master/', None),
}

# Generate labels in the format <page>:<section>
autosectionlabel_prefix_document = True
suppress_warnings = ['autosectionlabel.*']

# napoleon settings
napoleon_google_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_param = True
napoleon_type_aliases = {
    'DateOrInt': 'pyinaturalist.constants.DateOrInt',
    'IntOrStr': 'pyinaturalist.constants.IntOrStr',
    'MultiInt': 'pyinaturalist.constants.MultiInt',
    'MultiStr': 'pyinaturalist.constants.MultiStr',
}

# copybutton settings: Strip prompt text when copying code blocks
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True

# Move type hint info to function description instead of signature
autodoc_typehints = 'description'

# apidoc settings
apidoc_module_dir = PACKAGE_DIR
apidoc_output_dir = MODULE_DOCS_DIR
apidoc_excluded_paths = ['api_docs/*', 'models/*', 'node_api.py', 'rest_api.py']
apidoc_extra_args = ['--templatedir=_templates']
apidoc_module_first = True
apidoc_separate_modules = True
apidoc_toc_file = False

# autosummary + automodapi settings
automodapi_inheritance_diagram = False
automodapi_toctreedirnm = MODULE_DOCS_DIR
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
    'table_classes': ['docutils'],
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
    for stylesheet in glob(join(CSS_DIR, '*.css')):
        app.add_css_file(basename(stylesheet))


def setup_external_files(app):
    """Create symlinks and copies of files outside docs directory so they can be accessed by Sphinx
    directives.
    """
    make_symlink(SAMPLE_DATA_DIR, DATA_DIR_SYMLINK)
    # Unfortunately this can't be symlinked; nbsphinx will insert image links relative to this dir
    rmtree(NOTEBOOK_DIR_COPY, ignore_errors=True)
    copytree(EXAMPLES_DIR, NOTEBOOK_DIR_COPY)


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
