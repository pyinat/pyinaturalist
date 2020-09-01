from pyinaturalist.forge_utils import document_request_params, copy_docstrings, copy_signatures


def test_document_request_params():
    pass


def func_template():
    """
    arg_1: First test arg
    arg_2: Second test arg
    """


def test_copy_docstrings__with_return_desc():
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
    """.strip()

    modified_func = copy_docstrings(func, [func_template])
    assert modified_func.__doc__ == expected_docstring


def test_copy_docstrings__without_return_desc():
    def func():
        """ Test function. """

    expected_docstring = """
Test function.

Args:
    arg_1: First test arg
    arg_2: Second test arg
    """.strip()

    modified_func = copy_docstrings(func, [func_template])
    assert modified_func.__doc__ == expected_docstring


def test_copy_signatures():
    pass
