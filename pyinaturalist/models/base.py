# TODO: Inherit from UserDict so model objects can also be used like dicts?
#   e.g. support both observation['id'] and observation.id
import json
from datetime import datetime, timezone
from logging import getLogger
from os.path import expanduser
from pathlib import Path
from typing import IO, Dict, List, Type, TypeVar, Union

import attr

from pyinaturalist.constants import JsonResponse
from pyinaturalist.response_format import convert_lat_long, try_datetime

# Some aliases for common attribute types
kwarg = attr.ib(default=None)
coordinate_pair = attr.ib(converter=convert_lat_long, default=None)  # type: ignore
datetime_attr = attr.ib(converter=try_datetime, default=None)  # type: ignore
datetime_now_attr = attr.ib(converter=try_datetime, default=datetime.now(timezone.utc))  # type: ignore

T = TypeVar('T', bound='BaseModel')
logger = getLogger(__name__)


@attr.s
class BaseModel:
    """Base class for models"""

    partial: bool = kwarg

    # Note: when used as converters, mypy will raise a false positive error. See:
    # https://github.com/python/mypy/issues/6172
    # https://github.com/python/mypy/issues/7912
    @classmethod
    def from_json(cls: Type[T], value: JsonResponse, partial=False):
        """Create a new model object from a JSON path, file-like object, or API response object"""
        # Strip out Nones so we use our default factories instead (e.g. for empty lists)
        if not value:
            return cls()
        elif isinstance(value, dict):
            attr_names = attr.fields_dict(cls).keys()
            valid_json = {k: v for k, v in value.items() if k in attr_names and v is not None}
            return cls(**valid_json, partial=partial)  # type: ignore
        else:
            return cls.from_json(_load_path_or_obj(value))  # type: ignore

    @classmethod
    def from_json_list(cls: Type[T], value: Union[IO, str, JsonResponse]) -> List:
        """Initialize from a JSON path, file-like object, or API response"""
        if not value:
            return []
        elif isinstance(value, dict) and 'results' in value:
            value = value['results']
        elif isinstance(value, dict):
            value = [value]  # type: ignore
        if isinstance(value, list):
            return [cls.from_json(item) for item in value]
        else:
            return cls.from_json_list(_load_path_or_obj(value))  # type: ignore

    def to_json(self) -> Dict:
        return attr.asdict(self)


def _load_path_or_obj(value: Union[IO, Path, str]):
    if isinstance(value, (Path, str)):
        with open(expanduser(str(value))) as f:
            return json.load(f)
    else:
        return json.load(value)
