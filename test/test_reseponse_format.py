import pytest
from datetime import datetime
from dateutil.tz import tzoffset

from pyinaturalist.response_format import parse_observation_timestamp


@pytest.mark.parametrize(
    'timestamp, offset_str, output',
    [
        (
            'Sat Sep 26 2020 12:09:51 GMT-0700 (PDT)',
            None,
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset('PDT', 25200)),  # TODO: wait what
        ),
        (
            '2020-09-27 9:20:02 AM PDT',
            '-07:00',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset(None, -25200)),
        ),
    ],
)
def test_parse_timestamp(timestamp, offset_str, output):
    observation = {'observed_on_string': timestamp, 'time_zone_offset': offset_str}
    print(timestamp, '|', parse_observation_timestamp(observation))
    # assert False
