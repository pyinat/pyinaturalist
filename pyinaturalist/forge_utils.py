"""
Utilities built on top of ``python-forge`` used to simplify usage for API docs, mainly by
combining function signature modification with docstring modification.
"""
from inspect import cleandoc
from itertools import chain
from functools import wraps
from logging import getLogger
from typing import Callable, List

from pyinaturalist.constants import TemplateFunction

logger = getLogger(__name__)


def document_request_params(template_functions: List[TemplateFunction]):
    """Document a function with both docstrings and function signatures from one or more
    template functions.

    Signature modification requires ``python-forge``. If not installed, only docstrings will be modified.

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
    """
    template_functions = [*template_functions, _user_agent]

    def f(func):
        # Modify docstring
        func = copy_docstrings(func, template_functions)

        # If forge is installed, modify signature; otherwise, silently ignore it
        try:
            func = copy_signatures(func, template_functions)
        except ImportError:
            logger.debug("Forge not installed; skipping runtime API documentation")

        # Call modified function
        @wraps(func)
        def g(*args, **kwargs):
            return func(*args, **kwargs)

        return g

    return f


def copy_docstrings(
    target_function: Callable, template_functions: List[TemplateFunction]
) -> Callable:
    """Copy docstrings from one or more template functions to a target function.
    Assumes Google-style docstrings.

    Args:
        target_function: Function to modify
        template_functions: Functions containing docstrings to apply to ``target_function``
    """
    # Start with initial function description only
    docstring, return_value_desc = _split_docstring(target_function.__doc__ or "")

    # Insert 'Args' section
    docstring += "\n\nArgs:"
    for template_function in template_functions:
        docstring += template_function.__doc__ or ""
        docstring = docstring.rstrip()

    # Insert 'Returns' section, if present
    if return_value_desc:
        docstring += "\n\nReturns:\n    " + return_value_desc

    target_function.__doc__ = docstring
    return target_function


def _split_docstring(docstring):
    """ Split a docstring into a function description + return value description, if present. """
    if "Returns:" in docstring:
        function_desc, return_value_desc = docstring.split("Returns:")
    else:
        function_desc = docstring
        return_value_desc = ""

    return cleandoc(function_desc.strip()), cleandoc(return_value_desc.strip())


def copy_signatures(
    target_function: Callable, template_functions: List[TemplateFunction]
) -> Callable:
    """Copy function signatures from one or more template functions to a target function.

    Args:
        target_function: Function to modify
        template_functions: Functions containing params to apply to ``target_function``
    """
    revision = _get_combined_revision(template_functions)
    return revision(target_function)


def _get_combined_revision(template_functions: List[TemplateFunction]):
    """ Create a :py:class:`forge.Revision` from the combined parameters of multiple functions """
    import forge

    # Use forge.copy to create a revision for each template function
    revisions = [forge.copy(func) for func in template_functions]

    # Combine the parameters of all revisions into a single revision
    fparams = [list(rev.signature.parameters.values()) for rev in revisions]
    return forge.sign(*list(chain.from_iterable(fparams)))


# Param template that's added to every function signature by default
def _user_agent(user_agent: str = None):
    """
    user_agent: A custom user-agent string to provide to the iNaturalist API
    """
