# Minimal makefile for Sphinx documentation
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build


# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help all Makefile

all: clean symlink-images linkcheck html

# Create symlinks so that relative links to static content will resolve correctly in:
# 1. README.rst (as displayed on GitHub) and
# 2. Sphinx html docs (as displayed on readthedocs.io)
symlink-images:
	mkdir -p docs && rm docs/images
	ln -s $(pwd)/images $(pwd)/docs/images

# Catch-all target: route all unknown targets to Sphinx builder
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
