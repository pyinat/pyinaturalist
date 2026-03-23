"""Tests for typed field selection (FieldPath, FieldProxy, build_fields_dict)"""

import json
from unittest.mock import patch

import pytest

from pyinaturalist.models import Observation, Taxon
from pyinaturalist.models.field_path import (
    FieldPath,
    FieldProxy,
    build_fields_dict,
    contains_field_paths,
)
from pyinaturalist.v2 import get_observations


def test_field_path_repr():
    assert repr(FieldPath('id')) == "FieldPath('id')"
    assert repr(FieldPath('taxon', 'name')) == "FieldPath('taxon.name')"


def test_field_path_equality():
    assert FieldPath('id') == FieldPath('id')
    assert FieldPath('taxon', 'name') == FieldPath('taxon', 'name')
    assert FieldPath('id') != FieldPath('uuid')


def test_field_path_hashable():
    s = {FieldPath('id'), FieldPath('id'), FieldPath('uuid')}
    assert len(s) == 2


def test_field_proxy_chained():
    proxy = FieldProxy(Observation, prefix=())
    result = proxy.taxon.name
    assert isinstance(result, FieldPath)
    assert result == FieldPath('taxon', 'name')


def test_field_proxy_to_field_path():
    proxy = FieldProxy(Taxon, prefix=('taxon',))
    assert proxy.to_field_path() == FieldPath('taxon')


def test_class_level_scalar_field_returns_field_path():
    assert Observation.id == FieldPath('id')
    assert Observation.uuid == FieldPath('uuid')
    assert Observation.created_at == FieldPath('created_at')
    assert Observation.quality_grade == FieldPath('quality_grade')
    assert Taxon.name == FieldPath('name')
    assert Taxon.rank == FieldPath('rank')


def test_class_level_lazy_property_returns_field_proxy():
    result = Observation.taxon
    assert isinstance(result, FieldProxy)


def test_class_level_nested_access():
    assert Observation.taxon.name == FieldPath('taxon', 'name')
    assert Observation.taxon.rank == FieldPath('taxon', 'rank')
    assert Taxon.default_photo.url == FieldPath('default_photo', 'url')


def test_instance_access_unaffected():
    """Class-level FieldDescriptors must not break normal instance attribute access."""
    obs = Observation(id=42, quality_grade='research')
    assert obs.id == 42
    assert obs.quality_grade == 'research'

    obs.id = 99
    assert obs.id == 99


def test_instance_access_unaffected_inherited_field():
    """Fields inherited from BaseModel (id, uuid) work on instances of all subclasses."""
    from pyinaturalist.models import UserCount

    uc = UserCount(id=5, species_count=10)
    assert uc.id == 5
    assert uc.species_count == 10


@pytest.mark.parametrize(
    'fields, expected',
    [
        # Single scalar field
        ([FieldPath('id')], {'id': True}),
        # Single nested field
        ([FieldPath('taxon', 'name')], {'taxon': {'name': True}}),
        # Multiple nested fields with shared prefix are merged
        (
            [FieldPath('taxon', 'name'), FieldPath('taxon', 'rank')],
            {'taxon': {'name': True, 'rank': True}},
        ),
        # Multiple top-level fields
        (
            [FieldPath('id'), FieldPath('uuid')],
            {'id': True, 'uuid': True},
        ),
        # Proxy shorthand (no sub-field) -> include whole nested model
        ([FieldProxy(Taxon, prefix=('taxon',))], {'taxon': True}),
        # Mix of scalar and nested
        (
            [FieldPath('id'), FieldPath('taxon', 'name')],
            {'id': True, 'taxon': {'name': True}},
        ),
        # Nested path deeper than 2 levels
        (
            [FieldPath('taxon', 'default_photo', 'url')],
            {'taxon': {'default_photo': {'url': True}}},
        ),
        # Real class-level attribute access
        (
            [Observation.id, Observation.taxon.name, Observation.taxon.rank],
            {'id': True, 'taxon': {'name': True, 'rank': True}},
        ),
        # Class-level proxy shorthand
        ([Observation.taxon], {'taxon': True}),
    ],
)
def test_build_fields_dict(fields, expected):
    assert build_fields_dict(fields) == expected


def test_build_fields_dict_nested_overrides_scalar():
    """If both FieldProxy shorthand and sub-fields are given, the nested dict takes precedence."""
    result = build_fields_dict([FieldPath('taxon'), FieldPath('taxon', 'name')])
    assert result == {'taxon': {'name': True}}


def test_build_fields_dict_ignores_non_field_path():
    """Non-FieldPath/FieldProxy items in the list are silently ignored."""
    result = build_fields_dict(['id', Observation.uuid])
    assert result == {'uuid': True}


def test_contains_field_paths_true():
    assert contains_field_paths([Observation.id]) is True
    assert contains_field_paths([Observation.taxon]) is True
    assert contains_field_paths([FieldPath('x'), 'other']) is True


def test_contains_field_paths_false():
    assert contains_field_paths([]) is False
    assert contains_field_paths(['id', 'taxon']) is False
    assert contains_field_paths({'id': True}) is False
    assert contains_field_paths('all') is False
    assert contains_field_paths(None) is False


@patch('pyinaturalist.client.session.format_response')
@patch('requests.sessions.Session.send')
def test_get_observations__field_path_list(mock_send, mock_format):
    """FieldPath list is converted to the expected nested dict before sending."""
    get_observations(
        id=14150125,
        fields=[Observation.id, Observation.taxon.name, Observation.taxon.rank],
    )
    request_obj = mock_send.call_args[0][0]
    json_body = json.loads(request_obj.body.decode())
    assert json_body['fields'] == {
        'id': True,
        'taxon': {'name': True, 'rank': True},
    }
