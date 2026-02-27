"""Test signature copying functionality to validate behavior before simplifying implementation."""

import inspect
from typing import Literal, Optional, get_args, get_origin

from pyinaturalist.docs import (
    copy_doc_signature,
    document_controller_params,
    document_request_params,
)
from pyinaturalist.v1.messages import get_messages
from pyinaturalist.v1.observations import get_observation_histogram, get_observations
from pyinaturalist.v1.projects import get_projects
from pyinaturalist.v1.search import search


# Test template functions that mimic the real ones in templates.py
def _test_template_basic(
    param_a: str | None = None,
    param_b: int | None = None,
):
    """Args:
    param_a: First parameter description
    param_b: Second parameter description
    """


def _test_template_complex(
    param_c: list[str] | None = None,
    param_d: bool = False,
):
    """Args:
    param_c: Complex parameter with list type
    param_d: Boolean parameter with default
    """


def test_copy_single_template():
    @copy_doc_signature(_test_template_basic)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    # Check signature was copied
    sig = inspect.signature(target_function)
    assert 'param_a' in sig.parameters
    assert 'param_b' in sig.parameters
    assert sig.parameters['param_a'].annotation == Optional[str]
    assert sig.parameters['param_b'].annotation == Optional[int]
    assert sig.parameters['param_a'].default is None
    assert sig.parameters['param_b'].default is None

    # Check docstring was merged
    doc = target_function.__doc__
    assert 'Target function description.' in doc
    assert 'param_a: First parameter description' in doc
    assert 'param_b: Second parameter description' in doc


def test_copy_multiple_templates():
    @copy_doc_signature(_test_template_basic, _test_template_complex)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    # Check all parameters from both templates are present
    sig = inspect.signature(target_function)
    assert 'param_a' in sig.parameters
    assert 'param_b' in sig.parameters
    assert 'param_c' in sig.parameters
    assert 'param_d' in sig.parameters

    # Check docstring contains all parameter docs
    doc = target_function.__doc__
    assert 'param_a: First parameter description' in doc
    assert 'param_c: Complex parameter with list type' in doc
    assert 'param_d: Boolean parameter with default' in doc


def test_exclude_args():
    @copy_doc_signature(_test_template_basic, exclude_args=['param_b'])
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    sig = inspect.signature(target_function)
    assert 'param_a' in sig.parameters
    assert 'param_b' not in sig.parameters

    doc = target_function.__doc__
    assert 'param_a: First parameter description' in doc
    assert 'param_b: Second parameter description' not in doc


def test_description_only():
    @copy_doc_signature(_test_template_basic, description_only=True)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    sig = inspect.signature(target_function)
    params = list(sig.parameters.keys())
    assert params == ['kwargs']

    # Check only description is in docstring (no Args section)
    doc = target_function.__doc__
    assert 'Target function description.' in doc
    assert 'param_a' not in doc


def test_multiline_docstring():
    def _test_template_multiline(
        param_e: str,
    ):
        """Args:
        param_e: A parameter with a long description that spans
            multiple lines and should be preserved correctly
        """

    @copy_doc_signature(_test_template_multiline)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    doc = target_function.__doc__
    assert 'multiple lines and should be preserved' in doc


def test_add_common_args():
    @copy_doc_signature(_test_template_basic, add_common_args=True)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    sig = inspect.signature(target_function)
    assert 'dry_run' in sig.parameters
    assert 'session' in sig.parameters
    assert 'param_a' in sig.parameters  # Original template args should still be there


def test_include_sections():
    @copy_doc_signature(_test_template_basic, include_sections=['Description', 'Args'])
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    assert 'Target function description.' in target_function.__doc__
    assert 'param_a: First parameter description' in target_function.__doc__
    assert 'Return' not in target_function.__doc__  # Return section should be excluded


def test_document_request_params():
    @document_request_params(_test_template_basic)
    def api_function(**kwargs):
        """API function description."""
        return kwargs

    # Should have template args plus common args
    sig = inspect.signature(api_function)
    assert 'param_a' in sig.parameters
    assert 'param_b' in sig.parameters
    assert 'dry_run' in sig.parameters
    assert 'session' in sig.parameters


def test_document_controller_params():
    """Test that document_controller_params excludes controller-specific params."""

    def _controller_template(
        dry_run: bool = False,
        session=None,
        page: int | None = None,
        per_page: int | None = None,
        param_x: str | None = None,
    ):
        """Args:
        dry_run: Should be excluded
        session: Should be excluded
        page: Should be excluded
        per_page: Should be excluded
        param_x: Should be included
        """

    @document_controller_params(_controller_template)
    def controller_method(**kwargs):
        """Controller method description."""
        return kwargs

    # Should exclude controller-specific params but include others
    sig = inspect.signature(controller_method)
    assert 'param_x' in sig.parameters
    # These should be excluded by CONTROLLER_EXCLUDE_PARAMS
    assert 'dry_run' not in sig.parameters
    assert 'session' not in sig.parameters
    assert 'page' not in sig.parameters
    assert 'per_page' not in sig.parameters


def test_invalid_template_function():
    """Test behavior with invalid template functions."""

    # This should not crash the decorator (based on current implementation)
    @copy_doc_signature(None)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    # Function should still be callable even if template was invalid
    assert callable(target_function)


def test_empty_template_list():
    """Test behavior with empty template list."""

    @copy_doc_signature()
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    # Should not crash and function should still work
    assert callable(target_function)
    result = target_function(test=True)
    assert result == {'test': True}


def test_template_with_no_docstring():
    """Test template function with no docstring."""

    def template_no_doc(param: str = 'default'):
        pass  # No docstring

    @copy_doc_signature(template_no_doc)
    def target_function(**kwargs):
        """Target function description."""
        return kwargs

    # Should still copy signature even without docstring
    sig = inspect.signature(target_function)
    assert 'param' in sig.parameters


def test_observation_search_pattern():
    """Test the pattern used by observation search methods."""

    # Simulate the pattern from observation_controller.py
    def _observation_common(
        q: str | None = None,
        d1=None,
        d2=None,
    ):
        """Args:
        q: Search observation properties
        d1: Must be observed on or after this date
        d2: Must be observed on or before this date
        """

    def _only_id(only_id: bool | None = None):
        """Args:
        only_id: Return only the record IDs
        """

    @copy_doc_signature(_observation_common, _only_id)
    def search(**params):
        """Search observations"""
        return params

    # Check all parameters are present
    sig = inspect.signature(search)
    assert 'q' in sig.parameters
    assert 'd1' in sig.parameters
    assert 'd2' in sig.parameters
    assert 'only_id' in sig.parameters

    # Check function works
    result = search(q='test', only_id=True)
    # Our simplified implementation doesn't auto-fill defaults
    expected_keys = {'q', 'only_id'}
    assert set(result.keys()) == expected_keys
    assert result['q'] == 'test'
    assert result['only_id'] is True


def test_identification_pattern():
    """Test the pattern used by identification controller."""

    def _identification_params(
        current_taxon: bool | None = None,
        own_observation: bool | None = None,
    ):
        """Args:
        current_taxon: ID's taxon is the same it's observation's taxon
        own_observation: ID was added by the observer
        """

    def _pagination(
        page: int | None = None,
        per_page: int | None = None,
    ):
        """Args:
        page: Page number of results to return
        per_page: Number of results to return in a page
        """

    def _only_id_local(only_id: bool | None = None):
        """Args:
        only_id: Return only the record IDs
        """

    @copy_doc_signature(_identification_params, _pagination, _only_id_local)
    def search_identifications(**params):
        """Search identifications"""
        return params

    # All template parameters should be present
    sig = inspect.signature(search_identifications)
    assert 'current_taxon' in sig.parameters
    assert 'own_observation' in sig.parameters
    assert 'page' in sig.parameters
    assert 'per_page' in sig.parameters
    assert 'only_id' in sig.parameters


def _literal_values(annotation) -> set[str]:
    values = set()
    origin = get_origin(annotation)

    if origin is Literal:
        return {str(v) for v in get_args(annotation)}

    for arg in get_args(annotation):
        if arg is type(None):
            continue
        values |= _literal_values(arg)

    return values


def test_request_signatures_include_literal_choices():
    message_sig = inspect.signature(get_messages)
    assert _literal_values(message_sig.parameters['box'].annotation) == {'any', 'inbox', 'sent'}

    obs_histogram_sig = inspect.signature(get_observation_histogram)
    assert _literal_values(obs_histogram_sig.parameters['date_field'].annotation) == {
        'created',
        'observed',
    }
    assert _literal_values(obs_histogram_sig.parameters['interval'].annotation) == {
        'day',
        'hour',
        'month',
        'month_of_year',
        'week',
        'week_of_year',
        'year',
    }

    observation_sig = inspect.signature(get_observations)
    assert {'casual', 'needs_id', 'research'} <= _literal_values(
        observation_sig.parameters['quality_grade'].annotation
    )
    assert {'CC-BY', 'CC0'} <= _literal_values(observation_sig.parameters['license'].annotation)

    search_sig = inspect.signature(search)
    assert {'places', 'projects', 'taxa', 'users'} <= _literal_values(
        search_sig.parameters['sources'].annotation
    )

    project_sig = inspect.signature(get_projects)
    assert {'assessment', 'bioblitz', 'collection', 'umbrella'} <= _literal_values(
        project_sig.parameters['type'].annotation
    )
