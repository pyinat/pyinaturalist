#!/usr/bin/env python
"""Utilities to process inputs and outputs for image quality assessment"""
import json
import re
from logging import getLogger
from os import makedirs
from os.path import isfile, join
from time import sleep

import requests
import requests_cache
from rich.progress import track

from examples.observation_custom_ranking import (
    DATA_DIR,
    PHOTO_ID_PATTERN,
    load_observations_from_export,
)

IMAGE_DIR = join(DATA_DIR, 'images')
logger = getLogger(__name__)


def get_original_image_urls(df):
    """Given an image URL (of any size), return the URL for the largest size image"""

    def get_original_image_url(image_url):
        if not str(image_url).startswith('http'):
            return None
        for size in ('square', 'small', 'medium', 'large'):
            image_url = image_url.replace(size, 'original')
        return image_url

    urls = [get_original_image_url(url) for url in df['photo.url'].unique()]
    return sorted(filter(None, urls))


def get_image_path(image_url):
    """Determine the local image filename based on its URL"""
    match = re.match(PHOTO_ID_PATTERN, image_url)
    # If for some reason the URL is in an unexpected format, just use the URL resource path
    if match:
        filename = f'{match.group(1)}.{match.group(2)}'
    else:
        filename = image_url.rsplit('/', 1)[1]
    return join(IMAGE_DIR, filename)


def download_images(image_urls):
    """Download all of the specified images"""
    makedirs(IMAGE_DIR, exist_ok=True)
    session = requests.Session()
    for url in track(image_urls):
        image_path = get_image_path(url)
        if isfile(image_path):
            continue

        try:
            with requests_cache.disabled():
                r = session.get(url, allow_redirects=True)
            r.raise_for_status()
            with open(image_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logger.exception(e)


def load_iqa_report():
    """Load an image quality assessment report"""
    with open('downloads/iqa.json') as f:
        iqa = json.load(f)

    iqa = {int(i['image_id']): i['mean_score_prediction'] for i in iqa}
    iqa = dict(sorted(iqa.items(), key=lambda x: x[1]))
    return iqa


def main():
    df = load_observations_from_export()
    image_urls = get_original_image_urls(df)
    download_images(image_urls)


if __name__ == '__main__':
    main()
