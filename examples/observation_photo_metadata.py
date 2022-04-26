#!/usr/bin/env python3
"""
An example of getting photo metadata from observation photos, which is currently not available in
the API and must be done by web scraping.

Note that web scraping in general is not very reliable and is prone to breakage, so this script
may or may not work without modification. See ``examples/sample_data/photo_info.html`` for an
example of photo info HTML at time of writing.

Also note that photo metadata is only visible to logged in users, so an access token is required.
For more details on authentication, see:

* https://www.inaturalist.org/pages/api+reference#auth
* https://pyinaturalist.readthedocs.io/en/stable/user_guide.html#authentication


Extra dependencies:
    ``pip install beautifulsoup4``
"""
from pprint import pprint

import requests
from bs4 import BeautifulSoup

from pyinaturalist import get_access_token, get_observation

IGNORE_ATTRIBUTES = ['Associated observations', 'Sizes']
PHOTO_INFO_BASE_URL = 'https://www.inaturalist.org/photos'


def get_photo_metadata(photo_url, access_token):
    """Scrape content from a photo info URL, and attempt to get its metadata"""
    print(f'Fetching {photo_url}')
    photo_page = requests.get(photo_url, headers={'Authorization': f'Bearer {access_token}'})
    soup = BeautifulSoup(photo_page.content, 'html.parser')
    table = soup.find(id='wrapper').find_all('table')[1]

    metadata = {}
    for row in table.find_all('tr'):
        key = row.find('th').text.strip()
        value = row.find('td').text.strip()
        if value and key not in IGNORE_ATTRIBUTES:
            metadata[key] = value
    return metadata


def get_observation_photo_metadata(observation_id, access_token):
    """Attempt to scrape metadata from all photo info pages associated with an observation"""
    print(f'Fetching observation {observation_id}')
    obs = get_observation(observation_id)
    photo_ids = [photo['id'] for photo in obs.get('photos', [])]
    photo_urls = [f'{PHOTO_INFO_BASE_URL}/{id}' for id in photo_ids]
    print(f'{len(photo_urls)} photo URL(s) found')
    return [get_photo_metadata(url, access_token) for url in photo_urls]


# !! Replace values here !!
if __name__ == '__main__':
    observation_id = 99
    access_token = get_access_token(
        username='',
        password='',
        app_id='',
        app_secret='',
    )
    all_metadata = get_observation_photo_metadata(observation_id, access_token)
    pprint(all_metadata, indent=4)
