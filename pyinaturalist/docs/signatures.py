"""Utilities for modifying function signatures using ``python-forge``"""
from functools import partial
from inspect import Parameter, ismethod, signature
from logging import getLogger
from typing import Callable, Dict, Iterable, List, Optional, Type

import forge
from requests import Session

from pyinaturalist.constants import TemplateFunction
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_annotations, copy_docstrings

AUTOMETHOD_INIT = '.. automethod:: __init__'
CONTROLLER_EXCLUDE_PARAMS = ['dry_run', 'session', 'page', 'per_page', 'order', 'count_only']

logger = getLogger(__name__)


def copy_doc_signature(
    *template_functions: TemplateFunction,
    add_common_args: bool = False,
    description_only: bool = False,
    include_sections: Optional[Iterable[str]] = None,
    include_return_annotation: bool = True,
    exclude_args: Optional[Iterable[str]] = None,
) -> Callable:
    """Document a function with docstrings, function signatures, and type annotations from
    one or more template functions.

    If used with other decorators, this should go first (e.g., last in the call order).

    Example:
        >>> # 1. Template function with individual request params + docs
        >>> def get_foo_template(arg_1: str = None, arg_2: bool = False):
        >>>     '''Args:
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
        description_only: Only add the function description
        include_sections: Docstring sections to include; if not specified, all sections will be included
        include_return_annotation: Copy the return type annotation from the template function(s)
        exclude_args: Arguments to exclude from the new docstring
    """
    if add_common_args:
        template_functions += (_dry_run, _session)
    if description_only:
        include_sections = ['Description']

    def wrapper(func):
        try:
            if not description_only:
                func = copy_annotations(func, template_functions, include_return_annotation)
            func = copy_docstrings(func, template_functions, include_sections, exclude_args)
            if not description_only:
                func = copy_signatures(func, template_functions, exclude_args)
        # If for any reason one of these steps fail, just log the error and return the original function
        except Exception:
            logger.exception(f'Failed to modify {func.__name__}')
        return func

    return wrapper


# Alias specifically for basic request functions
document_request_params = partial(copy_doc_signature, add_common_args=True)

# Aliases specifically for controller functions
document_controller_params = partial(
    copy_doc_signature,
    include_sections=['Description', 'Args'],
    include_return_annotation=False,
    exclude_args=CONTROLLER_EXCLUDE_PARAMS,
)
document_controller_description = partial(
    copy_doc_signature,
    description_only=True,
)


def document_common_args(func):
    """Just add common args to a function's docstring without modifying the signature"""
    template_functions = (_dry_run, _session)
    func = copy_annotations(func, template_functions)
    func = copy_docstrings(func, template_functions)
    return func


def extend_init_signature(*template_functions: Callable) -> Callable:
    """A class decorator that behaves like :py:func:`.copy_doc_signature`, but modifies a class
    docstring and its ``__init__`` function signature, and extends them instead of replacing them.
    """

    def wrapper(target_class: Type):
        # Modify init signature + docstring
        revision = copy_doc_signature(*template_functions, target_class.__init__)
        target_class.__init__ = revision(target_class.__init__)

        # Include init docs in class docs
        target_class.__doc__ = target_class.__doc__ or ''
        if AUTOMETHOD_INIT not in target_class.__doc__:
            target_class.__doc__ += f'\n\n    {AUTOMETHOD_INIT}\n'
        return target_class

    return wrapper


def copy_signatures(
    target_function: Callable,
    template_functions: List[TemplateFunction],
    exclude_args: Optional[Iterable[str]] = None,
) -> Callable:
    """A decorator that copies function signatures from one or more template functions to a
    target function.

    Args:
        target_function: Function to modify
        template_functions: Functions containing params to apply to ``target_function``
    """
    # Start with 'self' parameter if this is an instance method
    fparams = {}
    if 'self' in signature(target_function).parameters or ismethod(target_function):
        fparams['self'] = forge.self

    # Add and combine parameters from all template functions, excluding duplicates, self, and *args
    for func in template_functions:
        new_fparams = {
            k: v
            for k, v in forge.copy(func).signature.parameters.items()
            if k != 'self' and v.kind != Parameter.VAR_POSITIONAL
        }
        fparams.update(new_fparams)

    # Manually remove any excluded parameters
    for key in ensure_list(exclude_args):
        fparams.pop(key, None)

    fparams = deduplicate_var_kwargs(fparams)
    revision = forge.sign(*fparams.values())
    return revision(target_function)


def deduplicate_var_kwargs(params: Dict) -> Dict:
    """Add variadic keyword args (e.g., ``**kwargs``) to the end of a function signature, accounting
    for any duplicates.
    """
    # Check for **kwargs by param type instead of by name
    for k, v in params.copy().items():
        if v.kind == Parameter.VAR_KEYWORD:
            params.pop(k)

    # Add **kwargs as the last param
    params.update(forge.kwargs)
    return params


# Templates for common params that are added to every request function by default
# ----------


def _dry_run(dry_run: Optional[bool] = False):
    """Args:
    dry_run: Just log the request instead of sending a real request
    """


def _session(session: Optional[Session] = None):
    """Args:
    session: An existing `Session object <https://docs.python-requests.org/en/latest/user/advanced/>`_ to use instead of creating a new one
    """
