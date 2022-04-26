from io import BytesIO
from typing import BinaryIO, Optional, Tuple

import requests

from pyinaturalist.constants import (
    ALL_LICENSES,
    CC_LICENSES,
    PHOTO_BASE_URL,
    PHOTO_CC_BASE_URL,
    PHOTO_INFO_BASE_URL,
    PHOTO_SIZES,
    TableRow,
)
from pyinaturalist.converters import format_dimensions, format_license
from pyinaturalist.models import BaseModel, define_model, field


@define_model
class Photo(BaseModel):
    """:fa:`camera` An observation photo, based on the schema of photos from:

    * `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_
    * `GET /taxa <https://api.inaturalist.org/v1/docs/#!/Taxa/get_taxa>`
    """

    attribution: str = field(default=None, doc='License attribution')
    license_code: str = field(
        default=None,
        converter=format_license,
        options=ALL_LICENSES,
        doc='Creative Commons license code',
    )
    original_dimensions: Tuple[int, int] = field(
        converter=format_dimensions, default=(0, 0), doc='Dimensions of original image'
    )
    url: str = field(default=None, doc='Image URL; see properties for URLs of specific image sizes')
    _url_format: str = field(init=False, repr=False, default=None)

    # Unused attributes
    # flags: List = field(factory=list)

    def __attrs_post_init__(self):
        # If there's no URL, make a guess based on ID and license:
        self.url = self.url or (
            f'{PHOTO_CC_BASE_URL}/{self.id}/original.jpg'
            if self.has_cc_license
            else f'{PHOTO_BASE_URL}/{self.id}?size=original'
        )

        # Get a URL format string to get different photo sizes. Note: default URL may be any size.
        for size in PHOTO_SIZES:
            if f'{size}.' in self.url:
                self._url_format = self.url.replace(size, '{size}')

    @property
    def dimensions_str(self) -> str:
        """Dimensions as a string, formatted as ``{width}x{height}``"""
        return f'{self.original_dimensions[0]}x{self.original_dimensions[1]}'

    @property
    def has_cc_license(self) -> bool:
        """Determine if this photo has a Creative Commons license"""
        return self.license_code in CC_LICENSES

    @property
    def info_url(self) -> str:
        """Photo info URL on iNaturalist.org"""
        return f'{PHOTO_INFO_BASE_URL}/{self.id}'

    @property
    def large_url(self) -> Optional[str]:
        """Image URL (large size)"""
        return self.url_size('large')

    @property
    def medium_url(self) -> Optional[str]:
        """Image URL (medium size)"""
        return self.url_size('medium')

    @property
    def mimetype(self) -> str:
        """MIME type of the image"""
        ext = self.url.lower().split('.')[-1].split('?')[0]
        ext = ext.replace('jpg', 'jpeg')
        return f'image/{ext}'

    @property
    def original_url(self) -> Optional[str]:
        """Image URL (original size)"""
        return self.url_size('original')

    @property
    def small_url(self) -> Optional[str]:
        """Image URL (small size)"""
        return self.url_size('small')

    @property
    def square_url(self) -> Optional[str]:
        """Image URL (thumbnail size)"""
        return self.url_size('square')

    @property
    def thumbnail_url(self) -> Optional[str]:
        """Image URL (thumbnail size)"""
        return self.url_size('square')

    def url_size(self, size: str) -> Optional[str]:
        size = size.replace('thumbnail', 'square').replace('thumb', 'square')
        if not self._url_format or size not in PHOTO_SIZES:
            return None
        return self._url_format.format(size=size)

    def open(self, size: str = 'large') -> BinaryIO:
        """Download the image and return as a file-like object"""
        url = self.url_size(size)
        return requests.get(url, stream=True).raw if url else BytesIO()

    def show(self, size: str = 'large'):
        """Download and display the image with the system's default image viewer.
        Requires ``pillow``.
        """
        from PIL import Image

        img = Image.open(self.open(size=size))
        img.show()

    @property
    def row(self) -> TableRow:
        return {
            'ID': self.id,
            'License': self.license_code,
            'Dimensions': self.dimensions_str,
            'URL': self.original_url,
        }

    def __str__(self) -> str:
        return f'[{self.id}] {self.original_url} ({self.license_code}, {self.dimensions_str})'
