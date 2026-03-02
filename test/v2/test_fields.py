"""Tests for pyinaturalist.v2.fields — FieldPath, FieldSelector, and conversion helpers."""

import pytest

from pyinaturalist.v2.fields import (
    FieldPath,
    FieldSelector,
    apply_except_fields,
    fields_to_dict,
    obs,
    taxon,
)

# ---------------------------------------------------------------------------
# FieldPath
# ---------------------------------------------------------------------------


def test_field_path__shallow():
    fp = FieldPath('species_guess')
    assert fp.to_dict() == {'species_guess': True}


def test_field_path__deep():
    fp = FieldPath('taxon.name')
    assert fp.to_dict() == {'taxon': {'name': True}}


def test_field_path__very_deep():
    fp = FieldPath('identifications.taxon.ancestors')
    assert fp.to_dict() == {'identifications': {'taxon': {'ancestors': True}}}


def test_field_path__repr():
    fp = FieldPath('taxon.name')
    assert repr(fp) == "FieldPath('taxon.name')"


def test_field_path__str():
    fp = FieldPath('taxon.name')
    assert str(fp) == 'taxon.name'


# ---------------------------------------------------------------------------
# FieldSelector
# ---------------------------------------------------------------------------


def test_field_selector__to_dict_shallow():
    """A selector with two leaf children should produce a merged dict."""
    selector = FieldSelector(
        'taxon',
        {'name': FieldPath('taxon.name'), 'id': FieldPath('taxon.id')},
    )
    result = selector.to_dict()
    assert result == {'taxon': {'name': True, 'id': True}}


def test_field_selector__to_dict_nested():
    """A nested selector should produce fully nested dicts."""
    inner = FieldSelector('taxon', {'name': FieldPath('identifications.taxon.name')})
    outer = FieldSelector('identifications', {'taxon': inner})
    result = outer.to_dict()
    assert result == {'identifications': {'taxon': {'name': True}}}


def test_field_selector__attributes_are_read_only():
    selector = FieldSelector('obs', {'id': FieldPath('id')})
    with pytest.raises(AttributeError):
        selector.id = FieldPath('something_else')


# ---------------------------------------------------------------------------
# _build_selector — module-level obs/taxon instances
# ---------------------------------------------------------------------------


def test_obs_has_scalar_field():
    """obs.species_guess should be a FieldPath."""
    assert isinstance(obs.species_guess, FieldPath)
    assert obs.species_guess.to_dict() == {'species_guess': True}


def test_obs_has_nested_selector():
    """obs.taxon should be a FieldSelector."""
    assert isinstance(obs.taxon, FieldSelector)


def test_obs_nested_leaf():
    """obs.taxon.name should be a FieldPath."""
    assert isinstance(obs.taxon.name, FieldPath)
    assert obs.taxon.name.to_dict() == {'taxon': {'name': True}}


def test_obs_deeply_nested_leaf():
    """obs.identifications.taxon should be a FieldSelector whose to_dict contains taxon fields."""
    result = obs.identifications.taxon
    assert isinstance(result, FieldSelector)
    d = result.to_dict()
    # to_dict() carries the full prefix: {'identifications': {'taxon': {...}}}
    assert 'taxon' in d.get('identifications', {})


def test_taxon_has_fields():
    """taxon selector should have at least name and rank."""
    assert hasattr(taxon, 'name')
    assert hasattr(taxon, 'rank')


def test_obs_to_dict_contains_expected_keys():
    """obs.to_dict() should include common top-level observation fields."""
    d = obs.to_dict()
    for key in ('taxon', 'user', 'identifications', 'photos', 'sounds'):
        assert key in d, f'Expected key {key!r} in obs.to_dict()'


def test_obs_to_dict_no_infinite_recursion():
    """Building the selector should not recurse infinitely for self-referential types."""
    # If this call completes without a RecursionError, the guard works
    d = obs.to_dict()
    assert isinstance(d, dict)


@pytest.mark.parametrize('selector', [obs.taxon.ancestors, obs.taxon.children])  # type: ignore[union-attr]
def test_taxon_cyclic_props_are_leaf(selector):
    """obs.taxon.ancestors and obs.taxon.children should be FieldPath leaves (cycle guard)."""
    assert isinstance(selector, FieldPath)


def test_identifications_taxon_ancestors_is_leaf():
    """obs.identifications.taxon.ancestors should be a FieldPath (cycle reached via different branch)."""
    assert isinstance(obs.identifications.taxon.ancestors, FieldPath)


def test_taxon_conservation_status_is_selector():
    """obs.taxon.conservation_status should be a FieldSelector (no longer blocked by depth limit)."""
    assert isinstance(obs.taxon.conservation_status, FieldSelector)


# ---------------------------------------------------------------------------
# fields_to_dict
# ---------------------------------------------------------------------------


def test_fields_to_dict__pass_through_string():
    assert fields_to_dict('all') == 'all'


def test_fields_to_dict__pass_through_none():
    assert fields_to_dict(None) is None


def test_fields_to_dict__pass_through_dict():
    d = {'taxon': {'name': True}}
    assert fields_to_dict(d) == d


def test_fields_to_dict__list_of_field_paths():
    result = fields_to_dict([FieldPath('taxon.name'), FieldPath('user.login')])
    assert result == {'taxon': {'name': True}, 'user': {'login': True}}


def test_fields_to_dict__obs_field_paths():
    result = fields_to_dict([obs.taxon.name, obs.user.login])
    assert result == {'taxon': {'name': True}, 'user': {'login': True}}


def test_fields_to_dict__plain_strings_in_list():
    """Plain strings in a list should be treated as top-level True values."""
    result = fields_to_dict(['id', 'species_guess'])
    assert result == {'id': True, 'species_guess': True}


def test_fields_to_dict__selector():
    """A FieldSelector in the list should expand to its full subtree."""
    result = fields_to_dict([obs.taxon])
    assert isinstance(result, dict)
    assert 'taxon' in result
    assert isinstance(result['taxon'], dict)


# ---------------------------------------------------------------------------
# apply_except_fields
# ---------------------------------------------------------------------------

_SIMPLE_BASE = {
    'id': True,
    'taxon': {'name': True, 'rank': True},
    'identifications': {
        'taxon': {
            'name': True,
            'ancestors': True,
        },
        'user': {'login': True},
    },
}


def test_apply_except_fields__plain_string_top_level():
    result = apply_except_fields(_SIMPLE_BASE, ['taxon'])
    assert 'taxon' not in result
    assert 'id' in result
    assert 'identifications' in result


def test_apply_except_fields__field_path_top_level():
    result = apply_except_fields(_SIMPLE_BASE, [FieldPath('taxon')])
    assert 'taxon' not in result


def test_apply_except_fields__nested_field_path():
    result = apply_except_fields(_SIMPLE_BASE, [FieldPath('identifications.taxon.ancestors')])
    assert 'identifications' in result
    assert 'taxon' in result['identifications']
    assert 'ancestors' not in result['identifications']['taxon']
    # Other sibling keys should remain
    assert 'name' in result['identifications']['taxon']


def test_apply_except_fields__field_selector_removes_subtree():
    """Excluding a FieldSelector should remove the named subtree."""
    result = apply_except_fields(_SIMPLE_BASE, [obs.identifications])
    assert 'identifications' not in result


def test_apply_except_fields__does_not_modify_original():
    """apply_except_fields must not mutate the base dict."""
    from copy import deepcopy

    original = deepcopy(_SIMPLE_BASE)
    apply_except_fields(_SIMPLE_BASE, ['taxon'])
    assert _SIMPLE_BASE == original


def test_apply_except_fields__missing_key_is_ignored():
    """Removing a non-existent key should not raise."""
    result = apply_except_fields(_SIMPLE_BASE, ['nonexistent'])
    assert result == _SIMPLE_BASE


def test_apply_except_fields__obs_nested_path():
    """Use obs selector to remove a nested path from obs.to_dict()."""
    base = obs.to_dict()
    result = apply_except_fields(base, [obs.identifications.taxon])
    assert 'identifications' in result
    assert 'taxon' not in result['identifications']


def test_apply_except_fields__obs_selector_removes_top_level():
    """Use obs.identifications selector to remove the entire identifications subtree."""
    base = obs.to_dict()
    result = apply_except_fields(base, [obs.identifications])
    assert 'identifications' not in result
