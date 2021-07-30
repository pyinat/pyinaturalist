from inspect import cleandoc

from pyinaturalist.docs import copy_docstrings


def func_template():
    """Args:
    arg_1: First test arg
    arg_2: Second test arg
    """


def test_copy_docstrings():
    def func():
        """Test function.

        Returns:
            None
        """

    expected_docstring = """
    Test function.

    Args:
        arg_1: First test arg
        arg_2: Second test arg

    Returns:
        None
    """

    modified_func = copy_docstrings(func, [func_template])
    assert modified_func.__doc__.strip() == cleandoc(expected_docstring.strip())


def test_copy_docstrings__extend_args():
    def func():
        """Test function.

        Args:
            arg_0: 0th test arg

        Returns:
            None
        """

    expected_docstring = """
    Test function.

    Args:
        arg_0: 0th test arg
        arg_1: First test arg
        arg_2: Second test arg

    Returns:
        None
    """

    modified_func = copy_docstrings(func, [func_template])
    assert modified_func.__doc__.strip() == cleandoc(expected_docstring.strip())


def test_copy_docstrings__without_returns():
    def func():
        """Test function."""

    expected_docstring = """
    Test function.

    Args:
        arg_1: First test arg
        arg_2: Second test arg
    """

    modified_func = copy_docstrings(func, [func_template])
    assert modified_func.__doc__.strip() == cleandoc(expected_docstring.strip())
