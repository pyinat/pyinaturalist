import pytest
from datetime import datetime
from dateutil.tz import tzoffset

from pyinaturalist.response_format import parse_observation_timestamp


@pytest.mark.parametrize(
    'timestamp, offset_str, expected_date',
    [
        (
            'Sat Sep 26 2020 12:09:51 GMT-0700 (PDT)',
            '-07:00',
            datetime(2020, 9, 26, 12, 9, 51, tzinfo=tzoffset(None, -25200)),
        ),
        (
            '2020-09-27 9:20:02 AM PST',
            'GMT-08:00',
            datetime(2020, 9, 27, 9, 20, 2, tzinfo=tzoffset(None, -28800)),
        ),
        (
            'Dec 04 2020 21:00:00 EET',
            'UTC +02:00',
            datetime(2020, 12, 4, 21, 0, 0, tzinfo=tzoffset(None, 7200)),
        ),
    ],
)
def test_parse_timestamp(timestamp, offset_str, expected_date):
    observation = {'observed_on_string': timestamp, 'time_zone_offset': offset_str}
    parsed_date = parse_observation_timestamp(observation)
    assert parsed_date == expected_date
