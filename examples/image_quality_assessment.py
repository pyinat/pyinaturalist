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
    CSV_COMBINED_EXPORT,
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


def append_iqa_scores(df):
    """Load image quality assessment scores and append to a dataframe of observation records"""
    # Sort user IDs by number of observations (in the current dataset) per user
    scores = load_iqa_scores()

    first_result = list(scores.values())[0]
    for key in first_result.keys():
        logger.info(f'Updating observations with {key}')
        df[key] = df['photo.id'].apply(lambda x: scores.get(x, {}).get(key))
    return df


def load_iqa_scores():
    """Load scores from one or more image quality assessment output files"""
    logger.info(f'Loading image quality assessment data')
    combined_scores = {}
    for file_path in IQA_REPORTS:
        with open(file_path) as f:
            scores = json.load(f)

        key = splitext(basename(file_path))[0]
        scores = {int(i['image_id']): {key: i['mean_score_prediction']} for i in scores}
        combined_scores.update(scores)

    combined_scores = dict(sorted(combined_scores.items(), key=lambda x: x[1][key]))
    return combined_scores


def main():
    # Download observation images
    df = load_observations_from_export()
    image_urls = get_original_image_urls(df)
    asyncio.run(download_images(image_urls))

    # TODO: Running IQA model goes here
    df = append_iqa_scores(df)
    df.to_csv(CSV_COMBINED_EXPORT)


if __name__ == '__main__':
    main()
