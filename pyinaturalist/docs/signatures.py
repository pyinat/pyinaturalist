"""Utilities for modifying function signatures using ``python-forge``"""
from functools import partial
from inspect import ismethod, signature
from logging import getLogger
from typing import Callable, Iterable, List

import forge
from pyrate_limiter import Limiter
from requests import Session

from pyinaturalist.constants import TemplateFunction
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_annotations, copy_docstrings

COMMON_PARAMS = ['dry_run', 'limiter', 'user_agent', 'session']
logger = getLogger(__name__)


def copy_doc_signature(
    *template_functions: TemplateFunction,
    add_common_args: bool = True,
    include_sections: Iterable[str] = None,
    include_return_annotation: bool = True,
    exclude_args: Iterable[str] = None,
) -> Callable:
    """Document a function with docstrings, function signatures, and type annotations from
    one or more template functions.

    If used with other decorators, this should go first (e.g., last in the call order).

    Example:

        >>> # 1. Template function with individual request params + docs
        >>> def get_foo_template(arg_1: str = None, arg_2: bool = False):
        >>>     '''
        >>>     arg_1: Example request parameter 1
        >>>     arg_2: Example request parameter 2
        >>>     '''

        >>> # 2. Decorated API Endpoint function with generic (variadic) keyword args
        >>> @document_request_params(get_foo_template)
        >>> def get_foo(**kwargs) -> List:
            ''' Get Foo resource '''

        >>> # 3. Modified function signature + docstring
        >>> help(get_foo)
        '''
        Help on function get_foo:
        get_foo(arg_1: str = None, arg_2: bool = False) -> List
        Get Foo resource
        Args:
            arg_1: Example request parameter 1
            arg_2: Example request parameter 2
        '''

    Args:
        template_functions: Template functions containing docstrings and params to apply to the
            wrapped function
        add_common_args: Add additional keyword arguments common to most functions
        include_sections: Docstring sections to include; if not specified, all sections will be included
        include_return_annotation: Copy the return type annotation from the template function(s)
        exclude_args: Arguments to exclude from the new docstring
    """
    if add_common_args:
        template_functions += (_dry_run, _limiter, _session, _user_agent)

    def wrapper(func):
        try:
            func = copy_annotations(func, template_functions, include_return_annotation)
            func = copy_docstrings(func, template_functions, include_sections, exclude_args)
            func = copy_signatures(func, template_functions, exclude_args)
        # If for any reason one of these steps fail, just log the error and return the original function
        except Exception:
            logger.exception(f'Failed to modify {func.__name__}')
        return func

    return wrapper


# Aliases specifically for basic request functions and controller functions, respectively
document_request_params = copy_doc_signature
document_controller_params = partial(
    copy_doc_signature,
    add_common_args=False,
    include_sections=['Description', 'Args'],
    include_return_annotation=False,
    exclude_args=COMMON_PARAMS,
)


def copy_signatures(
    target_function: Callable,
    template_functions: List[TemplateFunction],
    exclude_args: Iterable[str] = None,
) -> Callable:
    """Decorator to copy function signatures from one or more template functions to a target function.

    Args:
        target_function: Function to modify
        template_functions: Functions containing params to apply to ``target_function``
    """
    # Start with 'self' parameter if this is an instance method
    fparams = {}
    if 'self' in signature(target_function).parameters or ismethod(target_function):
        fparams['self'] = forge.self

    # Add and combine parameters from all template functions (also removes duplicates)
    for func in template_functions:
        fparams.update(forge.copy(func).signature.parameters)

    # Manually remove any excluded parameters
    for key in ensure_list(exclude_args):
        fparams.pop(key, None)

    revision = forge.sign(*fparams.values())
    return revision(target_function)


# Templates for common params that are added to every request function by default
# ----------


def _dry_run(dry_run: bool = False):
    """Args:
    dry_run: Just log the request instead of sending a real request
    """


def _limiter(limiter: Limiter = None):
    """Args:
    limiter: Custom rate limits to apply to this request
    """


def _session(session: Session = None):
    """Args:
    session: An existing `Session object <https://docs.python-requests.org/en/latest/user/advanced/>`_ to use instead of creating a new one
    """


def _user_agent(user_agent: str = None):
    """Args:
    user_agent: A custom user-agent string to provide to the iNaturalist API
    """
