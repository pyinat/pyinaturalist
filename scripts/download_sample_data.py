#!/usr/bin/env python
import json

from pyinaturalist import API_V1, API_V2, SAMPLE_DATA_DIR, ClientSession

session = ClientSession()


def download_sample_data():
    # V1
    write_response(
        f'{API_V1}/controlled_terms',
        SAMPLE_DATA_DIR / 'v1/get_controlled_terms.json',
    )
    write_response(
        f'{API_V1}/identifications/700305837',
        SAMPLE_DATA_DIR / 'v1/get_identifications_by_id.json',
    )
    write_response(
        f'{API_V1}/observations/16227955',
        SAMPLE_DATA_DIR / 'v1/get_observations_by_id.json',
    )
    write_response(
        f'{API_V1}/places/89191',
        SAMPLE_DATA_DIR / 'v1/get_places_by_id.json',
    )
    write_response(
        f'{API_V1}/projects/8348',
        SAMPLE_DATA_DIR / 'v1/get_projects_by_id.json',
    )
    write_response(
        f'{API_V1}/taxa/70118',
        SAMPLE_DATA_DIR / 'v1/get_taxa_by_id.json',
    )
    write_response(
        f'{API_V1}/taxa/580933',
        SAMPLE_DATA_DIR / 'v1/get_taxa_by_id_conservation_statuses.json',
    )
    write_response(
        f'{API_V1}/users/1',
        SAMPLE_DATA_DIR / 'v1/get_user_by_id.json',
    )

    # V2
    write_response(
        f'{API_V2}/observations/6448d03a-7f9a-4099-86aa-ca09a7740b00?fields=all',
        SAMPLE_DATA_DIR / 'v2/get_observations_by_id_full.json',
    )
    write_response(
        f'{API_V2}/places/89191?fields=all',
        SAMPLE_DATA_DIR / 'v2/get_places_by_id.json',
    )
    write_response(
        f'{API_V2}/projects/8348?fields=all',
        SAMPLE_DATA_DIR / 'v2/get_projects_by_id.json',
    )
    write_response(
        f'{API_V2}/taxa/70118?fields=all',
        SAMPLE_DATA_DIR / 'v2/get_taxa_by_id_full.json',
    )
    write_response(
        f'{API_V2}/users/1?fields=all',
        SAMPLE_DATA_DIR / 'v2/get_user_by_id.json',
    )


def write_response(url, output_path):
    try:
        response = session.get(url)
        output_path.write_text(json.dumps(response.json(), indent=2))
    except Exception:
        print(f'Error downloading {url}', exc_info=True)


if __name__ == '__main__':
    download_sample_data()
