#!/usr/bin/env python
"""[WIP] Utilities to get some relevant pieces of API info from its OpenAPI spec

Extra dependencies:
    ``pip install prance[osv] rich``
"""
import json
from os.path import isfile, join
from typing import Dict, List, Tuple

import requests
from prance import ResolvingParser
from rich import print

from pyinaturalist.constants import DOWNLOAD_DIR

SPEC_FILE = join(DOWNLOAD_DIR, 'swagger_v1.json')
SPEC_URL = 'https://api.inaturalist.org/v1/swagger.json'


def download_spec(force=False):
    """Download the OpenAPI spec, fix a couple issues that throw validation errors in osv/ssv,
    and write a modified copy with fully resolved references
    """
    if isfile(SPEC_FILE) and not force:
        print(f'Using previously downloaded OpenAPI spec: {SPEC_FILE}')
        return

    print(f'Downloading OpenAPI spec: {SPEC_URL}')
    spec = requests.get(SPEC_URL).json()

    spec['parameters']['ids_without_taxon_id']['name'] = 'ids_without_taxon_id'
    spec['parameters']['ids_without_observation_taxon_id']['name'] = 'ids_without_observation_taxon_id'
    spec['parameters']['projects_order_by']['default'] = 'created'

    with open(SPEC_FILE, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f'Modified and written to: {SPEC_FILE}')


def parse_spec():
    """Get path definitions from a parsed OpenAPI spec with all references resolved"""
    parser = ResolvingParser(SPEC_FILE)
    return parser.specification['paths']


def get_enum_params(endpoints) -> List[Tuple[str, str, str]]:
    """Find all request parameters with multiple-choice (enumerated) options"""
    return sorted(
        [
            (path, param['name'], param['enum'])
            for path, resource in endpoints.items()
            for endpoint in resource.values()
            for param in endpoint.get('parameters', [])
            if 'enum' in param
        ]
    )


def process_enum_params(enum_params) -> Tuple[Dict, Dict]:
    """Condense enumerated params into two categories:
    * Params with the same values across all endpoints
    * Params with different values for some endpoints
    """
    constant_enum_params = {name: options for (path, name, options) in enum_params}

    def has_multiple_enums(name, options):
        return any([n == name and o != options for (p, n, o) in enum_params])

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


def main():
    download_spec()
    endpoints = parse_spec()
    enum_params = get_enum_params(endpoints)
    constant_enum_params, variable_enum_params = process_enum_params(enum_params)
    print('[bold cyan]Constant multiple-choice params:[/bold cyan]', constant_enum_params)
    print('[bold cyan]Variable multiple-choice params:[/bold cyan]', variable_enum_params)


if __name__ == '__main__':
    main()
