# Documentation build configuration file, created by sphinx-quickstart
import os
import sys

cwd = os.getcwd()
parent = os.path.dirname(cwd)
sys.path.insert(0, parent)

import pyinaturalist

# -- General configuration -----------------------------------------------------

# Sphinx extension modules
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

# Enable automatic links to other projects' Sphinx docs
intersphinx_mapping = {
    "requests": ("https://requests.readthedocs.io/en/master/", None),
}

# Enable Google-style docstrings
napoleon_google_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = u"pyinaturalist"
copyright = u"2020, Nicolas Noé"

# The short X.Y version.
version = pyinaturalist.__version__
# The full version, including alpha/beta/rc tags.
release = pyinaturalist.__version__

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
# html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
