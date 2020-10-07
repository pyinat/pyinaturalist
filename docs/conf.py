# Documentation build configuration file, created by sphinx-quickstart
import sys
from os import makedirs, symlink
from os.path import abspath, dirname, exists, join

DOCS_DIR = abspath(dirname(__file__))
PROJECT_DIR = dirname(DOCS_DIR)
PACKAGE_DIR = join(PROJECT_DIR, "pyinaturalist")

# Source paths and symlink paths for static content to include
SRC_IMAGE_DIR = join(DOCS_DIR, "images")
SYMLINK_IMAGE_DIR = join(DOCS_DIR, "docs", "images")
SRC_DATA_DIR = join(PROJECT_DIR, "test", "sample_data")
SYMLINK_DATA_DIR = join(DOCS_DIR, "sample_data")

# Add project path so we can import our package
sys.path.insert(0, PROJECT_DIR)
from pyinaturalist import __version__

# General information about the project.
project = "pyinaturalist"
copyright = "2020, Nicolas Noé"
needs_sphinx = "3.0"
master_doc = "index"
source_suffix = [".rst", ".md"]
version = release = __version__
html_static_path = ["_static"]
templates_path = ["_templates"]

# Exclude the generated pyinaturalist.rst, which will just contain top-level __init__ info
# and add an extra level to the toctree
exclude_patterns = ["_build", "modules/pyinaturalist.rst"]

# Sphinx extension modules
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_automodapi.automodapi",
    "sphinx_automodapi.smart_resolver",
    "sphinxcontrib.apidoc",
    "m2r2",
]

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    "requests": ("https://requests.readthedocs.io/en/master/", None),
}

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Options for automodapi
automodsumm_inherited_members = False
autosummary_imported_members = False
numpydoc_show_class_members = False


# Use apidoc to auto-generate rst sources
# Added here instead of instead of in Makefile so it will be used by ReadTheDocs
apidoc_module_dir = PACKAGE_DIR
apidoc_output_dir = "modules"
apidoc_excluded_paths = ["api_docs.py"]
apidoc_module_first = True
apidoc_separate_modules = True
apidoc_toc_file = False

# Move type hint info to function description instead of signature;
# since we have some really long signatures, the default (`autodoc_typehints = "signature"`)
# becomes unreadable because all params + types get crammed into a single line.
autodoc_typehints = "description"
set_type_checking_flag = True

# HTML theme settings
pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"
# html_theme_options = {}

# Favicon & sidebar logo
# html_logo = 'logo.jpg'
# html_favicon = 'favicon.ico'


def setup(app):
    """Run some additional steps after the Sphinx builder is intialized.

    In addition to basic things like adding static resources, this allows us to run any custom
    behavior that would otherwise go in the Makefile, so the readthedocs builder will behave the
    same as building the docs manually.

    Reference:
        * https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
        * https://docs.readthedocs.io/en/stable/builds.html
        * https://github.com/sphinx-contrib/apidoc
    """
    app.connect("builder-inited", make_symlinks)
    app.connect("builder-inited", patch_automodapi)
    app.add_css_file("collapsible_container.css")


def make_symlinks(app):
    """Create symlinks so that relative links to static content will resolve correctly in both:
    * README.rst (as displayed on GitHub and PyPi) and
    * Sphinx html docs (as displayed on readthedocs.io)

    Also symlink sample response data so it can be used by both Sphinx and pytest
    """
    make_symlink(SRC_IMAGE_DIR, SYMLINK_IMAGE_DIR)
    make_symlink(SRC_DATA_DIR, SYMLINK_DATA_DIR)


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
