#!/usr/bin/env python
"""Parse the OpenAPI v2 spec and extract a nested field structure for a subset of relevant models"""

import json
import re
from pathlib import Path

SPECS_DIR = Path(__file__).parent / 'specs'
SPECS_DIR.mkdir(exist_ok=True)
SPEC_PATH = SPECS_DIR / 'openapi_spec_v2.json'
OUTPUT_PATH = SPECS_DIR / 'openapi_model_fields.json'

MODELS = [
    'Annotation',
    'ConservationStatus',
    'ControlledTerm',
    'Flag',
    'Identification',
    'ListedTaxon',
    'Observation',
    'ObservationField',
    'ObservationFieldValue',
    'Photo',
    'Place',
    'Project',
    'Sound',
    'Taxon',
    'User',
    'Vote',
]


def to_snake_case(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def extract_fields(
    schema: dict,
    spec: dict,
    visited: set[str] | None = None,
    scalars_only: bool = False,
) -> dict | bool:
    """
    Recursively extract fields from a schema.

    Args:
        schema: The schema definition to process
        spec: The full OpenAPI spec (for resolving $refs)
        visited: Set of schema names already visited in current path (for cycle detection)
        scalars_only: If True, don't follow $refs or recurse into nested objects (used for
            circular references)

    Returns:
        A dict of fields where scalars are True and objects are nested dicts,
        or True if this is a scalar.
    """
    if visited is None:
        visited = set()

    # Handle $ref
    if '$ref' in schema:
        if scalars_only:
            return True  # Don't follow refs in scalars_only mode
        ref_name = schema['$ref'].split('/')[-1]
        resolved = resolve_ref(schema['$ref'], spec)

        # Circular reference (i.e., taxon.ancestors)
        if ref_name in visited:
            return extract_fields(resolved, spec, visited, scalars_only=True)

        return extract_fields(resolved, spec, visited | {ref_name})

    schema_type = schema.get('type')

    # Scalar types
    if schema_type in ('string', 'integer', 'number', 'boolean'):
        return True

    # Arrays
    if schema_type == 'array':
        items = schema.get('items', {})
        if items.get('type') in ('string', 'integer', 'number', 'boolean'):
            return True
        if scalars_only:
            return {}  # Non-scalar array: exclude in scalars_only mode
        if not items:
            return True
        return extract_fields(items, spec, visited)

    # Objects
    if schema_type == 'object' or 'properties' in schema:
        properties = schema.get('properties', {})
        if not properties:
            return True

        result = {}
        for prop_name, prop_schema in sorted(properties.items()):
            # In scalars_only mode, skip $ref properties and nested objects
            if scalars_only and '$ref' in prop_schema:
                continue
            value = extract_fields(prop_schema, spec, visited, scalars_only)
            if value is True or not scalars_only:
                result[prop_name] = value
        return result if result else True

    return True


def resolve_ref(ref: str, spec: dict) -> dict:
    """Resolve a $ref string (ex: `#/components/schemas/Annotation`) to its schema definition"""
    parts = ref.removeprefix('#/').split('/')
    result = spec
    for part in parts:
        result = result[part]
    return result


def main():
    spec = json.loads(SPEC_PATH.read_text())
    schemas = spec['components']['schemas']

    all_fields = {}
    for model_name in MODELS:
        schema = schemas.get(model_name)
        if schema is None:
            print(f'Warning: schema {model_name!r} not found in spec, skipping')
            continue
        all_fields[to_snake_case(model_name)] = extract_fields(schema, spec)

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(all_fields, f, indent=2)
    print(f'Written to {OUTPUT_PATH}')


if __name__ == '__main__':
    main()
