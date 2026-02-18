#!/usr/bin/env python
"""Parse the OpenAPI v2 spec and extract a simplified RISON structure of Observation fields"""

import json
from pathlib import Path


def extract_fields(
    schema: dict,
    spec: dict,
    visited: set[str] | None = None,
) -> dict | bool:
    """
    Recursively extract fields from a schema.

    Args:
        schema: The schema definition to process
        spec: The full OpenAPI spec (for resolving $refs)
        visited: Set of schema names already visited in current path (for cycle detection)

    Returns:
        A dict of fields where scalars are True and objects are nested dicts,
        or True if this is a scalar.
    """
    if visited is None:
        visited = set()

    # Handle $ref
    if '$ref' in schema:
        ref_name = schema['$ref'].split('/')[-1]
        resolved = resolve_ref(schema['$ref'], spec)

        # Circular reference (i.e., taxon.ancestors)
        if ref_name in visited:
            return extract_scalar_fields_only(resolved)

        new_visited = visited | {ref_name}
        return extract_fields(resolved, spec, new_visited)

    schema_type = schema.get('type')

    # Scalar types
    if schema_type in ('string', 'integer', 'number', 'boolean'):
        return True

    # Arrays
    if schema_type == 'array':
        items = schema.get('items', {})
        if not items:
            return True
        if items.get('type') in ('string', 'integer', 'number', 'boolean'):
            return True
        return extract_fields(items, spec, visited)

    # Objects
    if schema_type == 'object' or 'properties' in schema:
        properties = schema.get('properties', {})
        if not properties:
            return True

        result = {}
        for prop_name, prop_schema in sorted(properties.items()):
            result[prop_name] = extract_fields(prop_schema, spec, visited)
        return result

    return True


def resolve_ref(ref: str, spec: dict) -> dict:
    """Resolve a $ref string (ex: `#/components/schemas/Annotation`) to its schema definition"""
    parts = ref.lstrip('#/').split('/')
    result = spec
    for part in parts:
        result = result[part]
    return result


def get_ref_name(ref: str) -> str:
    """Extract schema name from a $ref string."""
    return ref.split('/')[-1]


def extract_scalar_fields_only(schema: dict) -> dict | bool:
    """
    Extract only scalar fields from a schema (used for circular references).
    Does not follow any $refs or expand nested objects.
    """
    schema_type = schema.get('type')

    if schema_type in ('string', 'integer', 'number', 'boolean'):
        return True

    if schema_type == 'object' or 'properties' in schema:
        properties = schema.get('properties', {})
        if not properties:
            return True

        result = {}
        for prop_name, prop_schema in sorted(properties.items()):
            prop_type = prop_schema.get('type')
            if prop_type in ('string', 'integer', 'number', 'boolean'):
                result[prop_name] = True
            elif prop_type == 'array':
                items = prop_schema.get('items', {})
                if items.get('type') in ('string', 'integer', 'number', 'boolean'):
                    result[prop_name] = True

        return result if result else True

    return True


def main():
    repo_root = Path(__file__).parent.parent
    spec_path = repo_root / 'test/sample_data/openapi_spec_v2.json'
    output_path = repo_root / 'test/sample_data/obs_fields.json'

    with open(spec_path) as f:
        spec = json.load(f)
    observation_schema = spec['components']['schemas']['Observation']
    fields = extract_fields(observation_schema, spec)

    with open(output_path, 'w') as f:
        json.dump(fields, f, indent=2)
    print(f'Written to {output_path}')


if __name__ == '__main__':
    main()
