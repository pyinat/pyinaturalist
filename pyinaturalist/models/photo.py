from typing import List, Optional, Tuple

import attr


from pyinaturalist.constants import PHOTO_INFO_BASE_URL, PHOTO_SIZES
from pyinaturalist.models import BaseModel, kwarg
from pyinaturalist.request_params import CC_LICENSES
from pyinaturalist.response_format import format_dimensions, format_license


@attr.s
class Photo(BaseModel):
    """A data class containing information about a remote observation photo"""

    attribution: str = kwarg
    flags: List = attr.ib(factory=list)
    id: int = kwarg
    license_code: str = attr.ib(converter=format_license, default=None)  # Enum
    original_dimensions: Tuple[int, int] = attr.ib(converter=format_dimensions, default=(0, 0))
    url: str = kwarg
    _url_format: str = attr.ib(init=False, repr=False, default=None)

    def __attrs_post_init__(self):
        if not self.url:
            return

        # Get a URL format string to get different photo sizes
        for size in PHOTO_SIZES:
            if f'{size}.' in self.url:
                self._url_format = self.url.replace(size, '{size}')

    @property
    def has_cc_license(self) -> bool:
        """Determine if this photo has a Creative Commons license"""
        return self.license_code in CC_LICENSES

    @property
    def info_url(self) -> str:
        return f'{PHOTO_INFO_BASE_URL}/self.id'

    @property
    def large_url(self) -> Optional[str]:
        return self.url_size('large')

    @property
    def medium_url(self) -> Optional[str]:
        return self.url_size('large')

    @property
    def original_url(self) -> Optional[str]:
        return self.url_size('original')

    @property
    def small_url(self) -> Optional[str]:
        return self.url_size('small')

    @property
    def square_url(self) -> Optional[str]:
        return self.url_size('square')

    @property
    def thumbnail_url(self) -> Optional[str]:
        return self.url_size('square')

    def url_size(self, size: str) -> Optional[str]:
        size = size.replace('thumbnail', 'square').replace('thumb', 'square')
        if not self._url_format or size not in PHOTO_SIZES:
            return None
        return self._url_format.format(size=size)

    def open(self, size: str = 'large'):
        """Download and display the image with the system's default image viewer.
        Experimental / requires ``pillow``
        """
        import requests
        from PIL import Image

        url = self.url_size(size)
        if url:
            img = Image.open(requests.get(url, stream=True).raw)
            img.show()
