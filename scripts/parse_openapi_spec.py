#!/usr/bin/env python
"""Utilities to parse relevant schema details from iNat OpenAPI specs

Extra dependencies:
    ``pip install prance[osv] rich``
"""

import json
import re
from pathlib import Path

import requests
from prance import ResolvingParser
from rich import print

from pyinaturalist.constants import PathOrStr

SPECS_DIR = Path(__file__).parent / 'specs'
SPECS_DIR.mkdir(exist_ok=True)
SPEC_V1_URL = 'https://api.inaturalist.org/v1/swagger.json'
SPEC_V1_PATH = SPECS_DIR / 'openapi_spec_v1.json'
REQUEST_MODELS_V1_PATH = SPECS_DIR / 'openapi_request_models_v1.py'
RESPONSE_MODELS_V1_PATH = SPECS_DIR / 'openapi_response_models_v1.py'
ENUMS_V1_PATH = SPECS_DIR / 'openapi_enums_v1.py'

SPEC_V2_URL = 'https://api.inaturalist.org/v2/docs/swagger-ui-init.js'
SPEC_V2_PATH = SPECS_DIR / 'openapi_spec_v2.json'
REQUEST_MODELS_V2_PATH = SPECS_DIR / 'openapi_request_models_v2.py'
RESPONSE_MODELS_V2_PATH = SPECS_DIR / 'openapi_response_models_v2.py'
ENUMS_V2_PATH = SPECS_DIR / 'openapi_enums_v2.py'

STRING_FORMATS = {'date-time': 'datetime', 'date': 'date', 'binary': 'bytes'}
PRIMITIVE_TYPES = {'integer': 'int', 'number': 'float', 'boolean': 'bool', 'object': 'dict'}
MODELS_HEADER = """\
# Auto-generated classes from OpenAPI spec
from datetime import date, datetime
from typing import Any, Literal
"""


def download_v1_spec(force=False):
    """Download the V1 OpenAPI spec, fix some issues that throw validation errors in osv/ssv,
    and write a modified copy with fully resolved references
    """
    if SPEC_V1_PATH.is_file() and not force:
        print(f'Using previously downloaded OpenAPI spec: {SPEC_V1_PATH}')
        return

    print(f'Downloading OpenAPI spec: {SPEC_V1_URL}')
    spec = requests.get(SPEC_V1_URL).json()

    spec['parameters']['ids_without_taxon_id']['name'] = 'ids_without_taxon_id'
    spec['parameters']['ids_without_observation_taxon_id']['name'] = (
        'ids_without_observation_taxon_id'
    )
    spec['parameters']['projects_order_by']['default'] = 'created'

    # Remove duplicate parameters (by resolved name) within each operation.
    # Parameters may be $refs or inline; resolve the name for dedup purposes.
    def param_name(p: dict) -> str:
        return spec['parameters'][p['$ref'].split('/')[-1]]['name'] if '$ref' in p else p['name']

    for methods in spec['paths'].values():
        for op in methods.values():
            if isinstance(op, dict) and 'parameters' in op:
                seen: set[str] = set()
                op['parameters'] = [
                    p
                    for p in op['parameters']
                    if not (param_name(p) in seen or seen.add(param_name(p)))
                ]

    SPEC_V1_PATH.write_text(json.dumps(spec, indent=2))
    print(f'Modified and written to: {SPEC_V1_PATH}')


def download_v2_spec(force: bool = False) -> None:
    """Download and extract the v2 OpenAPI spec from the embedded swagger-ui-init.js page"""
    if SPEC_V2_PATH.is_file() and not force:
        print(f'Using previously downloaded OpenAPI v2 spec: {SPEC_V2_PATH}')
        return

    print(f'Downloading v2 swagger-ui-init.js: {SPEC_V2_URL}')
    js = requests.get(SPEC_V2_URL).text

    match = re.search(r'"swaggerDoc":\s*(\{)', js)
    if not match:
        raise ValueError('Could not find swaggerDoc in swagger-ui-init.js')

    spec, _ = json.JSONDecoder().raw_decode(js, match.start(1))
    SPEC_V2_PATH.write_text(json.dumps(spec, indent=2))
    print(f'Extracted and written to: {SPEC_V2_PATH}')


def parse_spec(spec_file: PathOrStr) -> dict:
    """Get path definitions from a parsed OpenAPI spec with all references resolved"""
    parser = ResolvingParser(str(spec_file))
    return parser.specification['paths']


def resolve_type(prop_schema: dict) -> str:
    """Map an OpenAPI property schema dict to a Python type string."""
    match prop_schema:
        case {} if not prop_schema:
            return 'Any'
        case {'$ref': ref}:
            return f"'{ref.split('/')[-1]}'"
        case {'anyOf': _} | {'oneOf': _}:
            return 'Any'
        case {'enum': values}:
            return f'Literal[{", ".join(repr(v) for v in values)}]'
        case {'type': 'array', 'items': items}:
            return f'list[{resolve_type(items)}]'
        case {'type': 'array'}:
            return 'list[Any]'
        case {'type': 'string', 'format': fmt}:
            return STRING_FORMATS.get(fmt, 'str')
        case {'type': 'string'}:
            return 'str'
        case {'type': t}:
            return PRIMITIVE_TYPES.get(t, 'Any')
        case _:
            return 'Any'


def generate_class(name: str, schema: dict) -> str:
    """Generate a Python class stub for a single OpenAPI schema definition."""
    lines = [f'class {name}:']
    props = schema.get('properties', {})
    if not props:
        lines.append('    pass')
    else:
        for prop_name, prop_schema in props.items():
            lines.append(f'    {prop_name}: {resolve_type(prop_schema)}')
    return '\n'.join(lines)


def _classify_schemas_v1(spec: dict) -> tuple[set[str], set[str]]:
    """Return (request_schemas, response_schemas) via flood-fill from endpoint refs.

    Works on the raw V1 Swagger 2.0 spec, where schemas live in 'definitions'
    and refs use '#/definitions/' prefixes.
    """
    schemas = spec['definitions']

    def refs_in(obj) -> set[str]:
        return set(re.findall(r'#/definitions/(\w+)', json.dumps(obj)))

    def expand(seeds: set[str]) -> set[str]:
        reachable = set(seeds)
        while frontier := {r for n in reachable for r in refs_in(schemas.get(n, {}))} - reachable:
            reachable |= frontier
        return reachable

    operations = [
        op for methods in spec['paths'].values() for op in methods.values() if isinstance(op, dict)
    ]
    request_seeds = {
        ref
        for op in operations
        for param in op.get('parameters', [])
        if isinstance(param, dict) and param.get('in') == 'body'
        for ref in refs_in(param.get('schema', {}))
    }
    response_seeds = {
        ref
        for op in operations
        for resp in op.get('responses', {}).values()
        if isinstance(resp, dict)
        for ref in refs_in(resp.get('schema', {}))
    }
    return expand(request_seeds), expand(response_seeds)


def _classify_schemas(spec: dict) -> tuple[set[str], set[str]]:
    """Return (request_schemas, response_schemas) via closure from endpoint refs.

    Items are collected from requestBody vs responses for each operation, then followed through
    $ref links within component schemas.
    """
    schemas = spec['components']['schemas']

    def refs_in(obj) -> set[str]:
        return set(re.findall(r'#/components/schemas/(\w+)', json.dumps(obj)))

    def expand(seeds: set[str]) -> set[str]:
        reachable = set(seeds)
        while frontier := {r for n in reachable for r in refs_in(schemas.get(n, {}))} - reachable:
            reachable |= frontier
        return reachable

    operations = [
        op for methods in spec['paths'].values() for op in methods.values() if isinstance(op, dict)
    ]
    request_seeds = {ref for op in operations for ref in refs_in(op.get('requestBody', {}))}
    response_seeds = {ref for op in operations for ref in refs_in(op.get('responses', {}))}
    response_seeds |= refs_in(spec['components'].get('responses', {}))

    return expand(request_seeds), expand(response_seeds)


def _write_models(schemas: dict, names: set[str], output_path: Path) -> None:
    """Write class stubs for the given schema names to output_path."""
    included = {name: schema for name, schema in schemas.items() if name in names}
    class_blocks = [generate_class(name, schema) for name, schema in included.items()]
    output_path.write_text(MODELS_HEADER + '\n\n' + '\n\n\n'.join(class_blocks) + '\n')
    print(f'Generated {len(included)} model classes -> {output_path}')


def generate_models_v1() -> None:
    """Generate Python class stubs from the v1 OpenAPI spec's schema definitions."""
    spec = json.loads(SPEC_V1_PATH.read_text())
    schemas = spec['definitions']
    request_schemas, response_schemas = _classify_schemas_v1(spec)

    _write_models(schemas, request_schemas, REQUEST_MODELS_V1_PATH)
    _write_models(schemas, response_schemas, RESPONSE_MODELS_V1_PATH)

    omitted = sorted(set(schemas.keys()) - request_schemas - response_schemas)
    print(f'Omitted {len(omitted)} unreferenced schemas: {omitted}')


def generate_models_v2():
    """Generate Python class stubs from the v2 OpenAPI spec's schema definitions."""
    spec = json.loads(SPEC_V2_PATH.read_text())
    schemas = spec['components']['schemas']
    request_schemas, response_schemas = _classify_schemas(spec)

    _write_models(schemas, request_schemas, REQUEST_MODELS_V2_PATH)
    _write_models(schemas, response_schemas, RESPONSE_MODELS_V2_PATH)

    omitted = sorted(set(schemas.keys()) - request_schemas - response_schemas)
    print(f'Omitted {len(omitted)} unreferenced schemas: {omitted}')


def get_enum_params(endpoints) -> list[tuple[str, str, list]]:
    """Find all request parameters with multiple-choice (enumerated) options.

    Handles both V1 (enum directly on param) and V2 (enum nested in param['schema']).
    """
    return sorted(
        [
            (path, param['name'], param.get('enum') or param.get('schema', {}).get('enum'))
            for path, resource in endpoints.items()
            for endpoint in resource.values()
            if isinstance(endpoint, dict)
            for param in endpoint.get('parameters', [])
            if 'enum' in param or 'enum' in param.get('schema', {})
        ]
    )


def process_enum_params(enum_params) -> tuple[dict, dict]:
    """Condense enumerated params into two categories:
    * Params with the same values across all endpoints
    * Params with different values for some endpoints
    """
    constant_enum_params = {name: options for (path, name, options) in enum_params}

    def has_multiple_enums(name, options):
        return any(n == name and o != options for (p, n, o) in enum_params)

    def get_all_enums(name):
        """Get all enums with the given parameter name, along with their parent endpoint paths"""
        return {p: o for (p, n, o) in enum_params if n == name}

    # Find any enumerated params with same name but different values per endpoint
    variable_enum_params = {
        name: get_all_enums(name)
        for name, options in constant_enum_params.items()
        if has_multiple_enums(name, options)
    }

    for name in variable_enum_params:
        constant_enum_params.pop(name)

    return constant_enum_params, variable_enum_params


def write_enum_params(constant_enum_params: dict, variable_enum_params: dict, output_path: Path):
    """Write enum params to a Python file."""
    lines = ['# Auto-generated enum parameter values from OpenAPI spec', '']

    lines.append('# Params with the same allowed values across all endpoints')
    lines.append('CONSTANT_ENUM_PARAMS = {')
    for name, options in sorted(constant_enum_params.items()):
        lines.append(f'    {name!r}: {options!r},')
    lines.append('}')

    lines.append('')

    lines.append('# Params with different allowed values depending on the endpoint')
    lines.append('VARIABLE_ENUM_PARAMS = {')
    for name, endpoints in sorted(variable_enum_params.items()):
        lines.append(f'    {name!r}: {{')
        for path, options in sorted(endpoints.items()):
            lines.append(f'        {path!r}: {options!r},')
        lines.append('    },')
    lines.append('}')

    output_path.write_text('\n'.join(lines) + '\n')
    print(f'Generated enum params -> {output_path}')


def generate_enums_v1():
    v1_endpoints = parse_spec(SPEC_V1_PATH)
    v1_enum_params = get_enum_params(v1_endpoints)
    constant_enum_params, variable_enum_params = process_enum_params(v1_enum_params)
    write_enum_params(constant_enum_params, variable_enum_params, ENUMS_V1_PATH)


def generate_enums_v2() -> None:
    spec = json.loads(SPEC_V2_PATH.read_text())
    v2_enum_params = get_enum_params(spec['paths'])
    constant_enum_params, variable_enum_params = process_enum_params(v2_enum_params)
    write_enum_params(constant_enum_params, variable_enum_params, ENUMS_V2_PATH)


def main():
    download_v1_spec()
    generate_enums_v1()
    generate_models_v1()

    download_v2_spec()
    generate_enums_v2()
    generate_models_v2()


if __name__ == '__main__':
    main()
