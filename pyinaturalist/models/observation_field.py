from datetime import date, datetime
from logging import getLogger
from typing import List, Union

from pyinaturalist.constants import TableRow
from pyinaturalist.converters import safe_split, try_date, try_datetime, try_int_or_float
from pyinaturalist.models import (
    BaseModel,
    LazyProperty,
    Taxon,
    User,
    datetime_now_field,
    define_model,
    field,
)

logger = getLogger(__name__)
# Mappings from observation field value datatypes to python types/conversion functions
OFV_DATATYPES = {
    'dna': str,
    'date': try_date,
    'datetime': try_datetime,
    'numeric': try_int_or_float,
    'taxon': int,
    'text': str,
    'time': str,
}
OFVValue = Union[date, datetime, float, int, str]


@define_model
class ObservationField(BaseModel):
    """:fa:`tag` An observation field **definition**, based on the schema of
    `GET /observation_fields <https://www.inaturalist.org/pages/api+reference#get-observation_fields>`_.
    """

    allowed_values: List[str] = field(converter=safe_split, factory=list)
    created_at: datetime = datetime_now_field(doc='Date and time the observation field was created')
    datatype: str = field(default=None)  # Enum
    description: str = field(default=None)
    name: str = field(default=None)
    updated_at: datetime = datetime_now_field(
        doc='Date and time the observation field was last updated'
    )
    user_id: int = field(default=None)
    users_count: int = field(default=None)
    uuid: str = field(default=None)
    values_count: int = field(default=None)

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Type': self.datatype,
            'Name': self.name,
            'Description': self.description,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'datatype', 'name', 'description']


@define_model
class ObservationFieldValue(BaseModel):
    """:fa:`tag` An observation field **value**, based on the schema of ``Observation.ofvs``
    from `GET /observations <https://api.inaturalist.org/v1/docs/#!/Observations/get_observations>`_.
    """

    datatype: str = field(default=None)  # Enum
    field_id: int = field(default=None)
    name: str = field(default=None)
    taxon_id: int = field(default=None)
    user_id: int = field(default=None)
    uuid: str = field(default=None)
    value: OFVValue = field(default=None)
    taxon: property = LazyProperty(
        Taxon.from_json, type=Taxon, doc='Taxon that the observation field applies to'
    )
    user: property = LazyProperty(
        User.from_json, type=User, doc='User that applied the observation field value'
    )

    # Unused attrbiutes
    # name_ci: str = field(default=None)
    # value_ci: int = field(default=None)

    # Convert value by datatype
    def __attrs_post_init__(self):
        if self.datatype in OFV_DATATYPES and self.value is not None:
            converter = OFV_DATATYPES[self.datatype]
            try:
                self.value = converter(self.value)
            except (TypeError, ValueError) as e:
                logger.debug(f'Failed to convert {self.name}="{self.value}" to {converter}: {e}')
                self.value = None

    @property
    def _row(self) -> TableRow:
        return {
            'ID': self.id,
            'Type': self.datatype,
            'Name': self.name,
            'Value': self.value,
        }

    @property
    def _str_attrs(self) -> List[str]:
        return ['id', 'datatype', 'name', 'value']
