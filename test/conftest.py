"""
Shared unit test-related utilities.
Pytest will also automatically pick up any fixtures defined here.
"""
import json
import os
import re
from inspect import getmembers, isfunction, signature, Parameter
from unittest.mock import MagicMock

HTTP_FUNC_PATTERN = re.compile(r"(get|put|post|delete)_.+")


def get_module_functions(module):
    """ Get all functions belonging to a module (excluding imports) """
    return {
        name: member
        for name, member in getmembers(module)
        if isfunction(member) and member.__module__ == module.__name__
    }


def get_module_http_functions(module):
    """ Get all functions belonging to a module and prefixed with an HTTP method """
    return {
        name: func for name, func in getmembers(module) if HTTP_FUNC_PATTERN.match(name.lower())
    }


def get_mock_args_for_signature(func):
    """ Automagically get a list of mock objects corresponding to the required arguments
    in a function's signature. Using ``inspect.Signature``, 'Required' is defined by:
    1. positional and 2. no default
    """
    required_args = [
        p
        for p in signature(func).parameters.values()
        if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        and p.default is Parameter.empty
    ]
    return [MagicMock()] * len(required_args)


def _sample_data_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_data", filename)


def load_sample_json(filename):
    with open(_sample_data_path(filename), encoding="utf-8") as fh:
        return json.load(fh)
