from datetime import date, datetime
from typing import List, Union

import attr

from pyinaturalist.models import BaseModel, Taxon, User, dataclass, datetime_now_attr, kwarg
from pyinaturalist.response_format import safe_split, try_int_or_float

# Mappings from observation field value datatypes to python datatypes
OFV_DATATYPES = {
    'dna': str,
    'date': date,
    'datetime': datetime,
    'numeric': try_int_or_float,
    'taxon': int,
    'text': str,
    'time': str,
}
OFVValue = Union[date, datetime, float, int, str]


@dataclass
class ObservationField(BaseModel):
    """A dataclass containing information about an observation field **definition**, matching the schema of
    `GET /observation_fields <https://www.inaturalist.org/pages/api+reference#get-observation_fields>`_.
    """

    allowed_values: List[str] = attr.ib(converter=safe_split, default=None)
    created_at: datetime = datetime_now_attr
    datatype: str = kwarg  # Enum
    description: str = kwarg
    id: int = kwarg
    name: str = kwarg
    updated_at: datetime = datetime_now_attr
    user_id: int = kwarg
    users_count: int = kwarg
    uuid: str = kwarg
    values_count: int = kwarg


@dataclass
class ObservationFieldValue(BaseModel):
    """A dataclass containing information about an observation field **value**, matching the schema of ``ofvs``
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    id: int = kwarg
    uuid: str = kwarg
    field_id: int = kwarg
    datatype: str = kwarg  # Enum
    name: str = kwarg
    value: OFVValue = kwarg
    user_id: int = kwarg
    taxon_id: int = kwarg

    # Nested model objects
    taxon: Taxon = attr.ib(converter=Taxon.from_json, default=None)  # type: ignore
    user: User = attr.ib(converter=User.from_json, default=None)  # type: ignore

    # Unused attrbiutes
    name_ci: str = kwarg
    value_ci: int = kwarg

    # Convert value by datatype
    def __attrs_post_init__(self):
        converter = OFV_DATATYPES[self.datatype]
        self.value = converter(self.value)


# The names are a little verbose, so let's alias them
OF = ObservationField
OFV = ObservationFieldValue


# def convert_ofv_by_datatype(value, datatype) -> OFVValue
