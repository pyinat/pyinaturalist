#!/usr/bin/env python
"""A script for mapping US state abbreviations and FIPS codes to iNaturalist place IDs"""

import csv
import logging
from pathlib import Path
from time import sleep

from pyinaturalist import iNatClient

DATA_DIR = Path(__file__).parent.parent / 'examples' / 'sample_data'
OUTPUT_FILE = DATA_DIR / 'us_state_place_ids.csv'
# Standard US state FIPS codes and full names.
# Source: https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
FIPS_CSV = DATA_DIR / 'us_state_fips_codes.csv'

PLACE_TYPE_STATE = 8  # iNat place_type value for US states

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def find_state_place_id(client: iNatClient, abbrev: str, full_name: str) -> int | None:
    """Search iNat autocomplete for the given state and return its place ID.

    Looks for a result with place_type == 8 (State) whose name matches the full state name.
    """
    results = client.places.autocomplete(q=full_name).all()
    for place in results:
        if place.place_type == PLACE_TYPE_STATE and full_name.lower() in place.name.lower():
            logger.info(f'  Matched: {place.display_name!r} (id={place.id})')
            return place.id
    # Fallback: accept any State-type result whose name starts with the full name
    for place in results:
        if place.place_type == PLACE_TYPE_STATE:
            logger.info(f'  Fallback match: {place.display_name!r} (id={place.id})')
            return place.id
    logger.warning(f'  No match found for {full_name!r} ({abbrev})')
    return None


def main() -> None:
    client = iNatClient()
    rows: list[dict[str, str | int]] = []

    with FIPS_CSV.open(newline='') as f:
        reader = csv.DictReader(f)
        state_codes = {
            row['state_abbrev']: (int(row['state_fips']), row['state_name']) for row in reader
        }
    total = len(state_codes)
    for i, (abbrev, (fips, full_name)) in enumerate(state_codes.items(), start=1):
        logger.info(f'[{i}/{total}] Searching for {full_name} ({abbrev}), FIPS={fips}')
        inat_id = find_state_place_id(client, abbrev, full_name)
        if inat_id is not None:
            rows.append({'state_abbrev': abbrev, 'state_fips': fips, 'inat_place_id': inat_id})
        sleep(0.5)

    rows.sort(key=lambda r: r['state_fips'])

    with OUTPUT_FILE.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['state_abbrev', 'state_fips', 'inat_place_id'])
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f'Wrote {len(rows)} rows to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
