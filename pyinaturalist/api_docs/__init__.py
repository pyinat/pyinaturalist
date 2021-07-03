# flake8: noqa: F401, F403
"""Utilities for generating pyinaturalist documentation, including:

* Dynamic docs: Function signatures + docstrings based on API request params
* Static docs: Sphinx documentation on readthedocs.io
"""
from pyinaturalist.api_docs.forge_utils import (
    copy_doc_signature,
    copy_docstrings,
    copy_signature,
    copy_signatures,
    document_request_params,
)
