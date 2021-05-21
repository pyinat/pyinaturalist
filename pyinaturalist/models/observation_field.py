from datetime import date, datetime
from typing import Dict, List, Optional, Union

from attr import define, field

from pyinaturalist.models import BaseModel, Taxon, User, cached_property, datetime_now_attr, kwarg
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


@define(auto_attribs=False)
class ObservationField(BaseModel):
    """A dataclass containing information about an observation field **definition**, matching the schema of
    `GET /observation_fields <https://www.inaturalist.org/pages/api+reference#get-observation_fields>`_.
    """

    allowed_values: List[str] = field(converter=safe_split, factory=list)
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


@define(auto_attribs=False)
class ObservationFieldValue(BaseModel):
    """A dataclass containing information about an observation field **value**, matching the schema of ``ofvs``
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    datatype: str = kwarg  # Enum
    field_id: int = kwarg
    id: int = kwarg
    name: str = kwarg
    taxon_id: int = kwarg
    user_id: int = kwarg
    uuid: str = kwarg
    value: OFVValue = kwarg

    # Lazy-loaded nested model objects
    _taxon: Dict = field(factory=dict, repr=False)
    _taxon_obj: Taxon = field(default=None, init=False, repr=False)
    _user: Dict = field(factory=dict, repr=False)
    _user_obj: User = field(default=None, init=False, repr=False)

    # Unused attrbiutes
    # name_ci: str = kwarg
    # value_ci: int = kwarg

    # Convert value by datatype
    def __attrs_post_init__(self):
        if self.datatype in OFV_DATATYPES and self.value is not None:
            converter = OFV_DATATYPES[self.datatype]
            self.value = converter(self.value)

    @cached_property
    def taxon(self) -> Optional[Taxon]:
        return Taxon.from_json(self._taxon) if self._taxon else None

    @cached_property
    def user(self) -> Optional[User]:
        return User.from_json(self._user) if self._user else None


# The names are a little verbose, so let's alias them
OF = ObservationField
OFV = ObservationFieldValue


# def convert_ofv_by_datatype(value, datatype) -> OFVValue
