# Documentation build configuration file, created by sphinx-quickstart
import sys
from os import makedirs, symlink
from os.path import abspath, dirname, exists, join
from shutil import copy, copytree, rmtree


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
IMAGE_DIR_SRC = join(DOCS_DIR, 'images')
IMAGE_DIR_SYMLINK = join(DOCS_DIR, 'docs', 'images')
DATA_DIR_SRC = join(PROJECT_DIR, 'test', 'sample_data')
DATA_DIR_SYMLINK = join(DOCS_DIR, 'sample_data')
NOTEBOOK_DIR_SRC = join(PROJECT_DIR, 'examples')
NOTEBOOK_DIR_COPY = join(DOCS_DIR, 'examples')

# Add project path so we can import our package
sys.path.insert(0, PROJECT_DIR)
from pyinaturalist import __version__  # noqa: E402

# General information about the project.
project = 'pyinaturalist'
copyright = '2021, Nicolas Noé, Jordan Cook'
needs_sphinx = '4.0'
master_doc = 'index'
source_suffix = ['.rst', '.md']
version = release = __version__
html_static_path = ['_static']
templates_path = ['_templates']

# Exclude the generated pyinaturalist.rst, which will just contain top-level __init__ info
# and add an extra level to the toctree
exclude_patterns = ['_build', 'modules/pyinaturalist.rst']

# Sphinx extension modules
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'sphinx_automodapi.automodapi',
    'sphinx_automodapi.smart_resolver',
    'sphinx_copybutton',
    'sphinx_rtd_theme',
    'sphinxcontrib.apidoc',
    'm2r2',
    'nbsphinx',
]

nbsphinx_allow_errors = True

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    'requests': ('https://requests.readthedocs.io/en/master/', None),
}

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Options for automodapi
automodsumm_inherited_members = False
autosummary_imported_members = False
numpydoc_show_class_members = False

# Strip prompt text when copying code blocks with copy button
copybutton_prompt_text = r'>>> |\.\.\. |\$ '
copybutton_prompt_is_regexp = True

# Use apidoc to auto-generate rst sources
# Added here instead of instead of in Makefile so it will be used by ReadTheDocs
apidoc_module_dir = PACKAGE_DIR
apidoc_output_dir = 'modules'
apidoc_excluded_paths = ['api_docs.py', 'models/*']
apidoc_module_first = True
apidoc_separate_modules = True
apidoc_toc_file = False

# Move type hint info to function description instead of signature;
# since we have some really long signatures, the default (`autodoc_typehints = 'signature'`)
# becomes unreadable because all params + types get crammed into a single line.
autodoc_typehints = 'description'
set_type_checking_flag = True

# HTML theme settings
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
# html_theme_options = {}

# Favicon & sidebar logo
# html_logo = 'logo.jpg'
# html_favicon = 'favicon.ico'


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
    app.connect('builder-inited', setup_external_files)
    app.connect('builder-inited', patch_automodapi)
    app.connect('build-finished', overwrite_subpackage_doc)
    app.add_css_file('collapsible_container.css')


def overwrite_subpackage_doc(app, exception):
    """This overwrites the auto-generated subpackage doc with a manually formatted one"""
    copy(join(DOCS_DIR, 'pyinaturalist.models.rst'), MODULE_DOCS_DIR)


def setup_external_files(app):
    """Create symlinks and copies of files outside docs directory so they can be accessed by Sphinx
    directives.
    """
    make_symlink(IMAGE_DIR_SRC, IMAGE_DIR_SYMLINK)
    make_symlink(DATA_DIR_SRC, DATA_DIR_SYMLINK)
    # Unfortunately this can't by symlinked; nbsphinx will insert image links relative to this dir
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
