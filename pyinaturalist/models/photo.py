from typing import BinaryIO, List, Optional, Tuple

import requests

from pyinaturalist.constants import (
    ALL_LICENSES,
    CC_LICENSES,
    ICON_SIZES,
    ICONIC_TAXA_BASE_URL,
    PHOTO_BASE_URL,
    PHOTO_CC_BASE_URL,
    PHOTO_INFO_BASE_URL,
    PHOTO_SIZES,
    JsonResponse,
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
    observation_id: int = field(default=None, doc='Associated observation ID')
    original_dimensions: Tuple[int, int] = field(
        converter=format_dimensions, default=(0, 0), doc='Dimensions of original image'
    )
    url: str = field(default=None, doc='Image URL; see properties for URLs of specific image sizes')
    user_id: int = field(default=None, doc='Associated user ID')
    uuid: str = field(default=None)
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

    @classmethod
    def from_json(cls, value: JsonResponse, **kwargs) -> 'Photo':
        """Flatten out potentially nested photo field before initializing"""
        if 'photo' in value:
            value = value['photo']
        return super(Photo, cls).from_json(value, **kwargs)

    @property
    def ext(self) -> str:
        """File extension from URL"""
        return self.url.lower().split('.')[-1].split('?')[0]

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
        return f'image/{self.ext.replace("jpg", "jpeg")}'

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
        url = self.url_size(size) or self.url
        return requests.get(url, stream=True).raw

    def show(self, size: str = 'large'):
        """Display the image with the system's default image viewer. Requires ``pillow``."""
        from PIL import Image

        img = Image.open(self.open(size=size))
        img.show()

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'License': self.license_code,
            'Dimensions': self.dimensions_str,
            'URL': self.original_url,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'license_code', 'url']


@define_model
class IconPhoto(Photo):
    """:fa:`camera` Class used for displaying an iconic taxon in place of a taxon photo"""

    iconic_taxon_name: str = field(default=None, doc='Iconic taxon name')

    def __attrs_post_init__(self):
        self._url_format = self.url.replace('.png', '-{size}px.png')
        self.url = self.medium_url

    @classmethod
    def from_iconic_taxon(cls, iconic_taxon_name: str):
        url = f'{ICONIC_TAXA_BASE_URL}/{iconic_taxon_name.lower()}.png'
        return cls(url=url)  # type: ignore  # A weird false positive as of mypy 0.950

    @property
    def icon_url(self) -> Optional[str]:
        """Image URL (32px icon size)"""
        return self.url_size('icon')

    def url_size(self, size: str) -> str:
        size = size.replace('thumbnail', 'square').replace('thumb', 'square')
        return self._url_format.format(size=ICON_SIZES.get(size, 'square'))

    @property
    def _str_attrs(self) -> List[str]:
        return ['iconic_taxon_name', 'url']
