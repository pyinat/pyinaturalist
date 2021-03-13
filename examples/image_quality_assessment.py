#!/usr/bin/env python
"""Utilities to process inputs and outputs for image quality assessment"""
import asyncio
import json
import re
from datetime import datetime
from logging import getLogger
from os import makedirs
from os.path import basename, isfile, join, splitext

import aiofiles
import aiohttp
import requests
import requests_cache
from rich.progress import Progress

from examples.observation_custom_ranking import (
    DATA_DIR,
    IQA_REPORTS,
    PHOTO_ID_PATTERN,
    load_observations_from_export,
)

IMAGE_DIR = join(DATA_DIR, 'images')
logger = getLogger(__name__)


def get_original_image_urls(df):
    """Given an image URL (of any size), return the URL for the largest size image"""
    logger.info('Getting image URLs')

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


async def download_images(urls):
    download_info = check_downloaded_images(urls)

    with Progress() as progress:
        # Set up progress bar
        task = progress.add_task("[cyan]Downloading...", total=len(urls))
        progress.update(task, advance=len(urls) - len(download_info))

        start_time = datetime.now()
        async with aiohttp.ClientSession() as session:
            tasks = [
                download_image(session, url, file_path, progress, task)
                for url, file_path in download_info.items()
            ]
            await asyncio.gather(*tasks)

    logger.info(f'Downloaded {len(urls)} images in {datetime.now() - start_time}s')


def check_downloaded_images(urls):
    """Get local file paths for URLs, and remove images that we've already downloaded"""
    makedirs(IMAGE_DIR, exist_ok=True)
    with Progress(transient=True) as progress:
        progress.console.print('Checking for completed downloads')
        task = progress.add_task("[cyan]Checking...", total=len(urls))
        download_info = {url: get_image_path(url) for url in urls}

        for url, path in list(download_info.items()):
            if isfile(path):
                download_info.pop(url)
            progress.update(task, advance=1)

        progress.console.print(
            f'{len(urls) - len(download_info)} images already downloaded, ',
            f'{len(download_info)} remaining',
        )

    return download_info


async def download_image(
    session: aiohttp.ClientSession, url: str, file_path: str, progress: Progress, task
):
    try:
        async with session.get(url) as response:
            assert response.status == 200
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(await response.read())
        progress.console.print(f'Downloaded {url} to {file_path}')
    except Exception as e:
        progress.console.print(f'Download for {url} failed: {str(e)}')

    progress.update(task, advance=1)


def load_iqa_report(file_path):
    """Load an image quality assessment report"""
    with open(file_path) as f:
        iqa = json.load(f)

    iqa = {int(i['image_id']): i['mean_score_prediction'] for i in iqa}
    iqa = dict(sorted(iqa.items(), key=lambda x: x[1]))
    return iqa


def main():
    df = load_observations_from_export()
    image_urls = get_original_image_urls(df)
    asyncio.run(download_images(image_urls))
    # load_iqa_report('downloads/iqa.json')


if __name__ == '__main__':
    main()
