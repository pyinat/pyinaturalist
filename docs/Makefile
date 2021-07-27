# Minimal makefile for Sphinx documentation
SPHINX_OPTS        ?= -j auto
AUTOBUILD_OPTS     = --ignore '*.csv' --ignore '**/Makefile' --ignore '**/modules/*' --port 8181 --open-browser
SOURCE_DIR         = .
APIDOC_SOURCE_DIRS = $(SOURCE_DIR)/api $(SOURCE_DIR)/models $(SOURCE_DIR)/modules
BUILD_DIR          = _build

# Put it first so that "make" without argument is like "make help".
help:
	sphinx-build -M help "$(SOURCE_DIR)" "$(BUILD_DIR)" $(SPHINX_OPTS) $(O)

.PHONY: help all clean-apidoc Makefile

all: clean clean-apidoc html


clean-apidoc:
	rm -rf $(APIDOC_SOURCE_DIRS)

livehtml:
	sphinx-autobuild "$(SOURCE_DIR)" "$(BUILD_DIR)"/html $(AUTOBUILD_OPTS) $(SPHINX_OPTS) $(O) 

# Catch-all target: route all unknown targets to Sphinx builder
%: Makefile
	sphinx-build -M $@ "$(SOURCE_DIR)" "$(BUILD_DIR)" $(SPHINX_OPTS) $(O)
	# E.g: sphinx-build -M html . _build
