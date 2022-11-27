# flake8: noqa: F401, F403
"""Utilities for generating pyinaturalist documentation, including:

* Dynamic docs: Function signatures + docstrings based on API request params
* Static docs: Sphinx documentation on readthedocs.io
"""
from pyinaturalist.docs.docstrings import ApiDocstring, copy_annotations, copy_docstrings
from pyinaturalist.docs.emoji import EMOJI
from pyinaturalist.docs.signatures import (
    copy_doc_signature,
    copy_signatures,
    document_common_args,
    document_controller_description,
    document_controller_params,
    document_request_params,
    extend_init_signature,
)
