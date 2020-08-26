# Documentation build configuration file, created by sphinx-quickstart
import sys
from os import makedirs, symlink
from os.path import abspath, dirname, exists, join

DOCS_DIR = abspath(dirname(__file__))
DOC_IMAGES_DIR = join(DOCS_DIR, "images")
PROJECT_DIR = dirname(DOCS_DIR)
PACKAGE_DIR = join(PROJECT_DIR, "pyinaturalist")
sys.path.insert(0, PROJECT_DIR)
from pyinaturalist import __version__

# General information about the project.
project = "pyinaturalist"
copyright = "2020, Nicolas Noé"
needs_sphinx = "3.0"
master_doc = "index"
source_suffix = ".rst"
version = release = __version__
# Exclude the generated pyinaturalist.rst, which will just contain top-level __init__ info
# and add an extra level to the toctree
exclude_patterns = ["_build", "modules/pyinaturalist.rst"]
html_static_path = ["_static"]
templates_path = ["_templates"]

# Sphinx extension modules
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.apidoc",
]

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    "requests": ("https://requests.readthedocs.io/en/master/", None),
}

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Use apidoc to auto-generate rst sources
apidoc_module_dir = PACKAGE_DIR
apidoc_output_dir = "modules"
apidoc_excluded_paths = ["__init__"]
apidoc_module_first = True
apidoc_separate_modules = True
apidoc_toc_file = False

# HTML theme settings
pygments_style = "sphinx"
html_theme = "sphinx_rtd_theme"
# html_theme_options = {}

# Favicon & sidebar logo
# html_logo = 'logo.jpg'
# html_favicon = 'favicon.ico'


def setup(app):
    """Run some additional steps after the Sphinx builder is intialized. This allows us to
    run any custom behavior that would otherwise go in the Makefile, so the readthedocs builder
    will behave the same as building the docs manually.

    Reference:
        * https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events
        * https://docs.readthedocs.io/en/stable/builds.html
        * https://github.com/sphinx-contrib/apidoc
    """
    app.connect("builder-inited", make_symlinks)


def make_symlinks(app):
    """Create symlinks so that relative links to static content will resolve correctly in both:
    * README.rst (as displayed on GitHub and PyPi) and
    * Sphinx html docs (as displayed on readthedocs.io)
    """
    doc_symlinks_dir = join(DOCS_DIR, "docs")
    symlinked_images_dir = join(doc_symlinks_dir, "images")
    makedirs(doc_symlinks_dir, exist_ok=True)
    if not exists(symlinked_images_dir):
        symlink(DOC_IMAGES_DIR, symlinked_images_dir)
