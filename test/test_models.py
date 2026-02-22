# ruff: noqa: F403
# TODO: Move most of these test cases to controller tests
"""Things to test for each model:

* Load with sample response JSON, make sure it doesn't explode
   * Test with responses from different endpoints and/or response variations, if applicable
* Initialize the model with no args, and expect sane defaults
* Any data type conversions that run on init
* Any additional properties or aliases on the model
* Formatting in the model's __str__ method
"""

from copy import deepcopy
from datetime import date, datetime

# ruff: noqa: F405
import pytest
from dateutil.tz import tzoffset, tzutc

from pyinaturalist.constants import (
    COMMON_RANKS,
    GBIF_TAXON_BASE_URL,
    ICONIC_TAXA,
    INAT_BASE_URL,
    PHOTO_BASE_URL,
    PHOTO_CC_BASE_URL,
    PHOTO_INFO_BASE_URL,
    PHOTO_SIZES,
    ROOT_TAXON_ID,
    UNRANKED,
)
from pyinaturalist.models import *
from test.conftest import sample_data_path
from test.sample_data import *

# Base
# --------------------


def test_from_json():
    obs = Observation.from_json(j_observation_1)
    assert obs.id == 16227955
    assert Observation.from_json(obs) is obs


def test_from_json_file():
    obs_list = Observation.from_json_file(sample_data_path('get_observations_v1_page1.json'))
    assert isinstance(obs_list, list)
    assert isinstance(obs_list[0], Observation)
    assert obs_list[0].id == 57754375
    assert Observation.from_json_file(None) == []


def test_from_json_list():
    obs_list = Observation.from_json_list(SAMPLE_DATA['get_observations_v1_page1'])
    assert isinstance(obs_list, list)
    assert isinstance(obs_list[0], Observation)
    assert obs_list[0].id == 57754375


def test_copy():
    obs_1 = Observation.from_json(j_observation_1)
    obs_2 = Observation.copy(obs_1)
    assert obs_1.id == obs_2.id and obs_1.taxon == obs_2.taxon

    # Make sure it's not a shallow copy
    obs_2.taxon.id = 1234
    assert obs_1.taxon.id != obs_2.taxon.id


def test_deepcopy():
    obs_1 = Observation.from_json(j_observation_1)
    obs_2 = deepcopy(obs_1)
    assert obs_1.id == obs_2.id and obs_1.taxon == obs_2.taxon
    obs_2.taxon.id = 1234
    assert obs_1.taxon.id != obs_2.taxon.id


def test_copy_collection():
    obs_list_1 = Observations.from_json([j_observation_1, j_observation_2])
    obs_list_2 = Observations.copy(obs_list_1)
    assert obs_list_1[0].id == obs_list_2[0].id and obs_list_1[0].taxon == obs_list_2[0].taxon
    obs_list_2[0].taxon.id = 1234
    assert obs_list_1[0].taxon.id != obs_list_2[0].taxon.id


def test_deduplicate():
    obs_list = Observations.from_json([j_observation_1, j_observation_1, j_observation_2])
    assert len(obs_list) == 3
    obs_list.deduplicate()
    assert len(obs_list) == 2


def test_to_dict():
    obs_dict = Observation.from_json(j_observation_1).to_dict()
    assert obs_dict['id'] == j_observation_1['id']
    assert obs_dict['user']['login'] == j_observation_1['user']['login']


def test_to_dict__specific_keys():
    keys = ['id', 'created_at', 'taxon']
    obs_dict = Observation.from_json(j_observation_1).to_dict(keys=['id', 'created_at', 'taxon'])
    assert list(obs_dict.keys()) == keys
    assert obs_dict['id'] == j_observation_1['id']
    assert isinstance(obs_dict['created_at'], datetime)
    assert obs_dict['taxon']['id'] == j_observation_1['taxon']['id']


@define
class ExampleModel(BaseModel):
    key: str = field(default=None)


def test_default_rich_repr():
    """If no __rich_repr__ or _str_attrs is defined, fall back to printing all attrs fields"""
    obj = ExampleModel(key='value')
    print_attrs = [a[0] for a in obj.__rich_repr__()]
    assert print_attrs == ['id', 'uuid', 'key']


# Conservation Statuses
# --------------------


@pytest.mark.parametrize(
    'status, iucn_id, authority, expected_name',
    [
        # IUCN Red List
        ('LC', None, 'IUCN', 'least concern'),
        ('vu', None, 'iucn', 'vulnerable'),
        # IUCN ID only
        (None, 0, None, 'not evaluated'),
        # NatureServe
        ('X', None, 'NatureServe', 'extinct'),
        ('2', None, 'NatureServe', 'imperiled'),
        ('G2', None, 'NatureServe', 'imperiled'),
        ('S2', None, 'NatureServe', 'imperiled'),
        ('S2S3', None, 'NatureServe', 'imperiled'),
        ('N2N4', None, 'NatureServe', 'vulnerable'),
        # Other authority using NatureServe format
        ('S3S4B', None, 'Vermont Fish & Wildlife', 'vulnerable'),
        # Norma Oficial
        ('A', None, 'norma_oficial_059', 'amenazada'),
        ('PR', None, 'Norma', 'sujeta a protección especial'),
        # Generic
        ('E', None, None, 'endangered'),
        ('LC', None, None, 'least concern'),
        ('sc', None, None, 'special concern'),
        # Unknown
        ('ASDF', None, None, 'placeholder status'),
        ('ASDF', None, 'NatureServe', 'placeholder status'),
        ('S2S9', None, 'NatureServe', 'placeholder status'),
    ],
)
def test_conservation_status__derived_status_name(status, iucn_id, authority, expected_name):
    cs = ConservationStatus(
        status=status,
        status_name='placeholder status',
        iucn=iucn_id,
        authority=authority,
    )
    assert cs.status_name == expected_name


def test_conservation_status__display_name():
    cs = ConservationStatus(
        status='S2S3B',
        iucn=2,
        authority='NatureServe',
        place=Place(name='Nova Scotia', display_name='Nova Scotia, CA'),
    )
    assert cs.display_name == 'imperiled (S2S3B) in Nova Scotia, CA'

    cs.place.display_name = None
    assert cs.display_name == 'imperiled (S2S3B) in Nova Scotia'

    cs.place = None
    assert cs.display_name == 'imperiled (S2S3B)'


def test_conservation_status__display_name_duplication():
    """Simplify a redundant display name like "extinct (EXTINCT)" """
    cs = ConservationStatus(
        status='extinct',
        status_name='extinct',
        iucn=70,
    )
    assert cs.display_name == 'extinct'


def test_conservation_status__original_status_name():
    cs_json = deepcopy(j_conservation_status)
    cs_json['status_name'] = 'replace_me'
    cs = ConservationStatus.from_json(cs_json)
    assert cs.status_name == 'imperiled'
    assert cs._original_status_name == 'replace_me'


def test_conservation_status__id_wrapper_properties():
    cs = ConservationStatus(place_id=1, user_id=2, updater_id=3)
    assert cs.place.id == cs.place_id == 1
    assert cs.user.id == cs.user_id == 2
    assert cs.updater.id == cs.updater_id == 3


def test_conservation_status__str():
    cs_json = deepcopy(j_conservation_status)
    cs_json['place'] = {'name': 'Test Location'}
    cs = ConservationStatus.from_json(cs_json)
    assert str(cs) == (
        'ConservationStatus(status_name=imperiled, status=S2B, authority=NatureServe, '
        'place_name=Test Location)'
    )


# Controlled Terms
# --------------------


def test_annotation__converters():
    annotation = Annotation.from_json(j_annotation_1)
    assert isinstance(annotation.user, User) and annotation.user.id == 886482


def test_annotation__empty():
    annotation = Annotation()
    assert annotation.votes == []
    assert annotation.user is None


def test_annotation__init_from_ids():
    annotation = Annotation(controlled_attribute_id=1, controlled_value_id=2)
    assert annotation.controlled_attribute.id == 1
    assert annotation.controlled_value.id == 2


def test_annotation__init_from_labels():
    annotation = Annotation(term='Life Stage', value='Adult')
    assert annotation.controlled_attribute.label == 'Life Stage'
    assert annotation.controlled_value.label == 'Adult'


def test_annotation__label_setters():
    annotation = Annotation(controlled_attribute={'id': 1}, controlled_value={'id': 2})
    annotation.term = 'Life Stage'
    annotation.value = 'Adult'
    assert annotation.controlled_attribute.label == 'Life Stage'
    assert annotation.controlled_value.label == 'Adult'


def test_annotation__str_with_labels():
    annotation = Annotation.from_json(j_annotation_1)
    assert str(annotation) == 'Annotation(term=Life Stage, value=Adult)'


def test_annotation__str_without_labels():
    annotation = Annotation(controlled_attribute_id=1, controlled_value_id=2)
    assert str(annotation) == 'Annotation(term=1, value=2)'


def test_controlled_term__converters():
    controlled_term = ControlledTerm.from_json(j_controlled_term_1)
    value = controlled_term.values[0]
    assert controlled_term.taxon_ids == [47126]
    assert isinstance(value, ControlledTermValue) and value.id == 21


def test_controlled_term__empty():
    controlled_term = ControlledTerm()
    assert controlled_term.taxon_ids == []
    assert controlled_term.values == []


def test_controlled_term__properties():
    controlled_term = ControlledTerm.from_json(j_controlled_term_1)
    assert controlled_term.value_labels == (
        'No Evidence of Flowering, Flowering, Fruiting, Flower Budding'
    )


def test_controlled_term__get_value_by_id():
    controlled_term = ControlledTerm.from_json(j_controlled_term_1)
    value = controlled_term.get_value_by_id(13)
    assert value.label == 'Flowering'
    assert controlled_term.get_value_by_id(999) is None


def test_controlled_term__str():
    controlled_term = ControlledTerm.from_json(j_controlled_term_1)
    assert str(controlled_term) == (
        'ControlledTerm(id=12, label=Plant Phenology, '
        'value_labels=No Evidence of Flowering, Flowering, Fruiting, Flower Budding)'
    )


def test_controlled_term__value():
    controlled_term_value = ControlledTermValue.from_json(j_controlled_term_value_1)
    assert controlled_term_value.taxon_ids == [47125]
    assert (
        str(controlled_term_value) == 'ControlledTermValue(id=21, label=No Evidence of Flowering)'
    )


def test_controlled_term_counts():
    controlled_term_counts = ControlledTermCounts.from_json(
        SAMPLE_DATA['get_observation_popular_field_values']
    )
    count_1 = controlled_term_counts[0]
    assert isinstance(count_1, ControlledTermCount)
    assert isinstance(count_1.controlled_attribute, ControlledTerm)
    assert isinstance(count_1.controlled_value, ControlledTermValue)
    assert count_1.term == 'Life Stage'
    assert count_1.value == 'Adult'


# Comments
# --------------------


def test_comment__converters():
    comment = Comment.from_json(j_comment_1)
    assert isinstance(comment.user, User) and comment.user.id == 2852555


def test_comment__empty():
    comment = Comment()
    assert isinstance(comment.created_at, datetime)
    assert comment.user is None


def test_comment__str():
    comment = Comment.from_json(j_comment_1)
    assert (
        str(comment)
        == 'Comment(id=5326888, username=samroom, created_at=Aug 28, 2020, truncated_body=Thankyou)'
    )


# Histogram
# --------------------


def test_histogram():
    histogram = Histogram.from_json(j_histogram_month_of_year)
    assert len(histogram) == 12
    assert histogram[0].label == 1
    assert histogram[0].formatted_label == 'Jan'
    assert histogram[0].count == 272
    assert histogram[0].interval == 'month_of_year'
    assert histogram[0].interval_column_label == 'Month'


# Identifications
# --------------------


def test_identification__converters():
    identification = ID.from_json(j_identification_3)
    assert isinstance(identification.user, User) and identification.user.id == 2852555


def test_identification__empty():
    identification = ID()
    assert isinstance(identification.created_at, datetime)
    assert identification.taxon is None
    assert identification.user is None


def test_identification__str():
    identification = ID.from_json(j_identification_3)
    assert str(identification) == (
        'Identification(id=126501311, username=samroom, taxon_name=Danaus plexippus (Monarch), '
        'created_at=Aug 27, 2020, truncated_body=)'
    )


# Life Lists
# --------------------


def test_life_list__converters():
    life_list = LifeList.from_json(j_life_list_1)
    assert life_list.data[0] == life_list[0]
    assert len(life_list) == 10
    assert life_list.count_without_taxon == 4
    assert isinstance(life_list.data[0], TaxonCount) and life_list.data[0].id == 48460

    # Should work with our without extra 'results' level from response JSON
    life_list = LifeList.from_json(j_life_list_1['results'])
    assert len(life_list) == 10
    assert life_list.count_without_taxon == 0


def test_life_list__empty():
    life_list = LifeList()
    assert life_list.data == []
    assert life_list._id_map is None


def test_life_list__get_count():
    life_list = LifeList.from_json(j_life_list_1)
    assert life_list.get_count(1) == 3023  # Animalia
    assert life_list.get_count(981) == 2  # Phasianus colchicus
    assert life_list.get_count(-1) == 4  # Observations with no taxon
    assert life_list.get_count(9999999) == 0  # Unobserved taxon


# Messages
# --------------------


def test_message__converters():
    message = Message.from_json(j_message)
    assert isinstance(message.to_user, User) and message.to_user.id == 2115051
    assert isinstance(message.from_user, User) and message.from_user.id == 12345


def test_message__empty():
    message = Message()
    assert message.thread_flags == []
    assert message.to_user is None
    assert message.from_user is None


def test_message__str():
    message = Message.from_json(j_message)
    assert str(message) == '[12345] Sent Sep 02, 2019 from test_user to jkcook: Re: Test Message'


# Observations
# --------------------


def test_observation__converters():
    obs = Observation.from_json(j_observation_2)
    utc = tzoffset('Etc/UTC', 0)
    assert obs.created_at == datetime(2020, 8, 27, 18, 0, 51, tzinfo=utc)
    assert obs.observed_on == datetime(2020, 8, 27, 8, 57, 22, tzinfo=utc)

    assert isinstance(obs.comments[0], Comment) and obs.comments[0].id == 5326888
    assert isinstance(obs.identifications[0], ID) and obs.identifications[0].id == 126501311
    assert isinstance(obs.photos[0], Photo) and obs.photos[0].id == 92152429
    assert isinstance(obs.taxon, Taxon) and obs.taxon.id == 48662
    assert isinstance(obs.user, User) and obs.user.id == 2852555

    assert obs.location == (50.0949055, -104.71929167)
    assert obs.private_location == (50.0949055, -104.71929167)


def test_observation__empty():
    obs = Observation()
    assert isinstance(obs.created_at, datetime)
    assert obs.comments == []
    assert obs.identifications == []
    assert obs.photos == []
    assert obs.uuid is None
    assert obs.taxon is None
    assert obs.user is None


def test_observation__application():
    obs = Observation.from_json(j_observation_v2)
    app = obs.application
    assert isinstance(app, Application)
    assert app.name == 'iNaturalist iPhone App'
    assert app.url.startswith('https://itunes.apple.com')
    assert (
        str(app)
        == 'Application(id=3, name=iNaturalist iPhone App, url=https://itunes.apple.com/us/app/inaturalist/id421397028?mt=8)'
    )


def test_observation__flags():
    obs_json = deepcopy(j_observation_v2)
    obs_json['flags'] = [j_flag_1]
    obs = Observation.from_json(obs_json)
    flag = obs.flags[0]
    assert isinstance(flag, Flag)
    assert flag.id == 123456
    assert flag.resolved is False
    assert flag.user.login == 'some_user'
    assert str(flag) == 'Flag(id=123456, flag=spam, resolved=False, username=some_user)'


def test_observation__ofvs():
    obs = Observation.from_json(j_observation_3_ofvs)
    ofv = obs.ofvs[0]
    assert isinstance(ofv, ObservationFieldValue)
    assert ofv.id == 14106828
    assert ofv.user.id == 2115051
    assert ofv.updater_id == 2115051


def test_observation__project_observations():
    obs = Observation.from_json(j_observation_3_ofvs)
    proj_obs = obs.project_observations[0]
    assert isinstance(proj_obs, ProjectObservation) and proj_obs.id == 48899479


def test_observation__quality_metrics():
    obs = Observation.from_json(j_observation_6_metrics)

    metric = obs.quality_metrics[0]
    assert isinstance(metric, QualityMetric)
    assert metric.id == 6988064
    assert metric.metric == 'wild'
    assert metric.agree is True
    assert metric.user.login == 'jkcook'
    assert str(metric) == 'QualityMetric(id=6988064, metric=wild, agree=True, username=jkcook)'

    vote = obs.votes[0]
    assert isinstance(vote, Vote)
    assert vote.vote_flag is True
    assert vote.user.login == 'jkcook'
    assert str(vote) == 'Vote(id=2115051, vote_flag=True, username=jkcook)'

    fave = obs.faves[0]
    assert isinstance(fave, Fave)
    assert fave.vote_flag is True
    assert fave.user.login == 'jkcook'
    assert str(fave) == 'Fave(id=2115052, vote_flag=True, username=jkcook)'


def test_observation__default_photo():
    obs = Observation.from_json(j_observation_2)
    assert (
        obs.default_photo.original_url
        == 'https://static.inaturalist.org/photos/92152429/original.jpg?1598551272'
    )


def test_observation__missing_default_photo():
    obs = Observation.from_json(j_observation_2)
    obs.photos = []
    assert obs.default_photo.original_url.endswith('insecta-200px.png')


def test_observation__missing_default_photo_and_taxon():
    obs = Observation.from_json(j_observation_2)
    obs.photos = []
    obs.taxon = None
    assert obs.default_photo.original_url.endswith('unknown-200px.png')


@pytest.mark.parametrize(
    'obs, expected',
    [
        (Observation(location=(50.646894, 4.360086)), '(50.6469, 4.3601)'),
        (
            Observation(location=(41.6532861424, -93.6965336266), geoprivacy='obscured'),
            '(41.6533, -93.6965) (obscured)',
        ),
        (
            Observation(location=(50.0, -100.0), private_location=(51.1111, -101.2222)),
            '(51.1111, -101.2222)',
        ),
        (Observation(), 'N/A'),
    ],
)
def test_observation__formatted_location(obs, expected):
    assert obs.formatted_location == expected


def test_observation__ident_taxon_ids():
    obs = Observation.from_json(j_observation_2)
    assert obs.ident_taxon_ids == [
        1,
        372739,
        48663,
        48460,
        47120,
        47922,
        184884,
        47157,
        47158,
        522900,
        47224,
        134169,
        48662,
        61244,
    ]


def test_observation__ident_taxon_ids__current_only():
    obs = Observation.from_json(j_observation_2)
    obs.identifications[1].current = False
    obs.identifications[1].taxon.id = 123456
    assert obs.ident_taxon_ids == [
        1,
        372739,
        48663,
        48460,
        47120,
        47922,
        184884,
        47157,
        47158,
        522900,
        47224,
        134169,
        48662,
        61244,
    ]


def test_observation__cumulative_ids__all_agree():
    obs = Observation.from_json(j_observation_2)
    assert obs.cumulative_ids == (2, 2)


def test_observation__cumulative_ids__most_agree():
    obs = Observation.from_json(j_observation_2)

    # Add a dissenting ID from a different family
    tiger_swallowtail = Taxon(
        id=60551,
        ancestor_ids=[
            48460,
            1,
            47120,
            372739,
            47158,
            184884,
            47157,
            47224,
            47223,
            49973,
            207785,
            47225,
            545186,
        ],
    )
    obs.identifications.append(Identification(taxon=tiger_swallowtail, current=True))
    assert obs.cumulative_ids == (2, 3)


def test_observation__add_ancestors():
    obs = Observation.from_json(j_observation_2)
    assert [f'{t.rank} {t.name}' for t in obs.taxon.ancestors] == [
        'kingdom Animalia',
        'phylum Arthropoda',
        'subphylum Hexapoda',
        'class Insecta',
        'subclass Pterygota',
        'order Lepidoptera',
        'superfamily Papilionoidea',
        'family Nymphalidae',
        'subfamily Danainae',
        'tribe Danaini',
        'subtribe Danaina',
        'genus Danaus',
    ]


OBS_IGNORE_ATTRS = [
    'cached_votes_total',
    'comments_count',
    'created_at_details',
    'created_time_zone',
    'faves_count',
    'geojson',
    'ident_taxon_ids',
    'map_scale',
    'non_owner_ids',
    'observation_photos',
    'observed_on_details',
    'observed_on_string',
    'observed_time_zone',
    'spam',
    'time_zone_offset',
]


def test_observation__taxon_obj():
    obs_json = deepcopy(j_observation_2)
    obs_json['taxon'] = Taxon.from_json(obs_json['taxon'])
    for attr in OBS_IGNORE_ATTRS:
        obs_json.pop(attr, None)
    obs = Observation(**obs_json)
    assert isinstance(obs.taxon, Taxon) and obs.taxon.id == 48662


def test_observations():
    obs_list = Observations.from_json_list(
        [j_observation_1, j_observation_1, j_observation_2, j_observation_3_ofvs]
    )
    assert isinstance(obs_list.identifiers[0], User) and len(obs_list.identifiers) == 6
    assert isinstance(obs_list.observers[0], User) and len(obs_list.observers) == 3
    assert isinstance(obs_list.photos[0], Photo) and len(obs_list.photos) == 4
    assert isinstance(obs_list.taxa[0], Taxon) and len(obs_list.taxa) == 3
    assert (
        obs_list.photos[0].thumbnail_url
        == 'https://static.inaturalist.org/photos/24355315/square.jpeg?1536150664'
    )


# Observation Fields
# --------------------


def test_observation_field__converters():
    obs_field = ObservationField.from_json(j_obs_field_1)
    assert obs_field.allowed_values == ['Male', 'Female', 'Unknown']
    assert obs_field.created_at == datetime(2016, 5, 29, 16, 17, 8, 51000, tzinfo=tzutc())


def test_observation_field__empty():
    obs_field = ObservationField()
    assert obs_field.allowed_values == []
    assert isinstance(obs_field.created_at, datetime)


def test_observation_field__str():
    obs_field = ObservationField.from_json(j_obs_field_1)
    assert (
        str(obs_field)
        == 'ObservationField(id=4813, datatype=text, name=Sex (deer/turkey), description=)'
    )


def test_observation_field_value__numeric():
    ofv = OFV.from_json(j_ofv_1_numeric)
    assert ofv.datatype == 'numeric'
    assert ofv.value == 100
    assert ofv.taxon is None
    assert isinstance(ofv.user, User) and ofv.user.id == 2115051


def test_observation_field_value__taxon():
    ofv = OFV.from_json(j_ofv_2_taxon)
    assert ofv.datatype == 'taxon'
    assert ofv.value == 119900
    assert isinstance(ofv.taxon, Taxon) and ofv.taxon.id == 119900


def test_observation_field_value__date():
    ofv = OFV.from_json(j_ofv_3_date)
    assert ofv.datatype == 'date'
    assert ofv.value == date(2022, 11, 9)
    assert ofv.taxon is None


def test_observation_field_value__datetime():
    ofv = OFV.from_json(j_ofv_4_datetime)
    assert ofv.datatype == 'datetime'
    assert ofv.value == datetime(2022, 11, 9, 11, 20, 42)
    assert ofv.taxon is None


def test_observation_field_value__converter_error():
    ofv = OFV(datatype='taxon', value='birb')
    assert ofv.value is None


def test_observation_field_value__empty():
    ofv = OFV()
    assert ofv.value is None
    assert ofv.taxon is None


def test_observation_field_value__str():
    ofv = OFV.from_json(j_ofv_2_taxon)
    assert (
        str(ofv)
        == 'ObservationFieldValue(id=14106828, datatype=taxon, name=Feeding on, value=119900)'
    )


# Photos
# --------------------


def test_photo__converters():
    photo = Photo.from_json(j_photo_1)
    assert photo.id == 38359335
    assert photo.license_code == 'CC-BY-NC'
    assert photo.original_dimensions == (2048, 1365)
    assert photo.info_url == f'{PHOTO_INFO_BASE_URL}/38359335'


def test_photo__empty():
    photo = Photo()
    assert photo.original_dimensions == (0, 0)


def test_photo__guess_url():
    photo = Photo(id=123)
    assert photo.url == f'{PHOTO_BASE_URL}/123?size=original'
    photo = Photo(id=123, license_code='CC-BY-NC')
    assert photo.url == f'{PHOTO_CC_BASE_URL}/123/original.jpg'


def test_photo__properties():
    photo = Photo.from_json(j_photo_1)
    assert photo.mimetype == 'image/jpeg'
    assert photo.dimensions_str == '2048x1365'
    assert photo.info_url == f'{PHOTO_INFO_BASE_URL}/38359335'


def test_photo__license():
    photo = Photo.from_json(j_photo_1)
    assert photo.has_cc_license is True
    photo.license_code = 'CC0'
    assert photo.has_cc_license is True

    photo.license_code = None
    assert photo.has_cc_license is False
    photo.license_code = 'ALL RIGHTS RESERVED'
    assert photo.has_cc_license is False


@pytest.mark.parametrize('size', PHOTO_SIZES)
def test_photo__urls(size):
    photo = Photo.from_json(j_photo_1)
    assert (
        photo.url_size(size)
        == getattr(photo, f'{size}_url')
        == f'https://static.inaturalist.org/photos/38359335/{size}.jpg?1557348751'
    )
    assert photo.url_size('embiggened') is None


def test_photo__str():
    photo = Photo.from_json(j_photo_1)
    assert str(photo) == (
        'Photo(id=38359335, license_code=CC-BY-NC, '
        'url=https://static.inaturalist.org/photos/38359335/square.jpg?1557348751)'
    )


# Places
# --------------------


def test_place__converters():
    place = Place.from_json(j_place_1)
    assert place.category is None
    assert place.location == (-43.3254578926, 172.2325124165)


def test_place__ancestry():
    place_json = deepcopy(j_place_1)
    place_json['ancestry'] = '1/2/3/4'
    place = Place.from_json(place_json)
    assert place.ancestor_place_ids == ['1', '2', '3', '4']


def test_place__empty():
    place = Place()
    assert place.ancestor_place_ids == []
    assert place.bounding_box_geojson == {}
    assert place.geometry_geojson == {}


def test_place_from_json_list__empty():
    assert Place.from_json_list([]) == []


def test_places__nearby():
    """Results from /places/nearby should have an extra 'category' attribute"""
    places = Place.from_json_list(j_places_nearby)
    assert places[0].category == 'standard'
    assert places[-1].category == 'community'


# Projects
# --------------------


def test_project__converters():
    project = Project.from_json(j_project_1)
    assert project.id == 8291
    assert project.title == 'PNW Invasive Plant EDDR'
    assert project.location == (48.777404, -122.306929)
    assert isinstance(project.user, User) and project.user.id == 233188
    assert str(project) == 'Project(id=8291, title=PNW Invasive Plant EDDR)'


def test_project__empty():
    project = Project()
    assert project.admins == []
    assert isinstance(project.created_at, datetime)
    assert project.location is None
    assert project.project_observation_rules == []
    assert project.search_parameters == []
    assert project.user is None


def test_project_observation_fields():
    project = Project.from_json(j_project_3_obs_fields)
    assert len(project.project_observation_fields) == 3
    pof = project.project_observation_fields[0]
    assert isinstance(pof, ProjectObservationField)
    assert pof.project_observation_field_id == 18
    assert pof.position == 0
    assert pof.required is False
    assert pof.id == 30
    assert pof.name == 'Group size'
    assert pof.datatype == 'numeric'


def test_project_user():
    project = Project.from_json(j_project_3_obs_fields)
    assert len(project.admins) == 3
    admin = project.admins[0]
    assert isinstance(admin, ProjectUser)
    assert admin.project_id == 407
    assert admin.project_user_id == 3737
    assert admin.role == 'curator'
    assert admin.id == 9042
    assert admin.login == 'mhill'


# Search
# --------------------


def test_search__empty():
    search_result = SearchResult()
    assert search_result.score == 0
    assert search_result.matches == []
    assert search_result.record is None


def test_search__place():
    search_result = SearchResult.from_json(j_search_result_2_place)
    assert search_result.score == 7.116488
    assert isinstance(search_result.record, Place) and search_result.record.id == 113562


def test_search__project():
    search_result = SearchResult.from_json(j_search_result_3_project)
    assert search_result.score == 6.9390197
    assert isinstance(search_result.record, Project) and search_result.record.id == 9978


def test_search__taxon():
    search_result = SearchResult.from_json(j_search_result_1_taxon)
    assert search_result.score == 9.062307
    assert isinstance(search_result.record, Taxon) and search_result.record.id == 47792


def test_search__user():
    search_result = SearchResult.from_json(j_search_result_4_user)
    assert search_result.score == 4.6454225
    assert isinstance(search_result.record, User) and search_result.record.id == 113886


# Sound
# --------------------


def test_sound__converters():
    sound = Sound.from_json(j_sound_1)
    assert sound.license_code == 'CC0'


def test_sound__aliases():
    sound = Sound.from_json(j_sound_1)
    url = 'https://static.inaturalist.org/sounds/263113.wav?1624793769'
    assert sound.url == sound.file_url == url
    assert sound.mimetype == sound.file_content_type == 'audio/x-wav'


def test_sound__nested_record():
    sound = Sound.from_json(j_sound_2_nested)
    assert sound.uuid == '5c858ffa-696b-4bf2-beab-9f519901bd17'
    assert sound.url.startswith('https://static.inaturalist.org/')
    assert isinstance(sound.created_at, datetime)
    assert isinstance(sound.updated_at, datetime)


# Taxa
# --------------------


def test_taxon__converters():
    taxon = Taxon.from_json(j_taxon_2_partial)
    assert isinstance(taxon.default_photo, Photo) and taxon.default_photo.id == 38359335


def test_taxon__empty():
    taxon = Taxon()
    assert taxon.preferred_common_name == ''
    assert taxon.iconic_taxon_name == 'Unknown'
    assert taxon.ancestors == []
    assert taxon.children == []
    assert taxon.taxon_photos == []


def test_taxon__str():
    # Rank, name, and common name
    taxon_1 = Taxon(id=3, name='Aves', preferred_common_name='birb', rank='class')
    assert str(taxon_1) == 'Taxon(id=3, full_name=Class Aves (Birb))'

    # Rank and name
    taxon_2 = Taxon(id=3, name='Aves', rank='class')
    assert str(taxon_2) == 'Taxon(id=3, full_name=Class Aves)'

    # Name only
    taxon_3 = Taxon(id=3, name='Aves')
    assert str(taxon_3) == 'Taxon(id=3, full_name=Aves)'

    # ID only
    taxon_4 = Taxon(id=12345)
    assert str(taxon_4) == 'Taxon(id=12345, full_name=12345)'

    # Apostrophe in common name
    taxon_5 = Taxon(
        id=137338523,
        name='Trachelipus rathkii',
        preferred_common_name='rathke’s woodlouse',
        rank='species',
    )
    assert str(taxon_5) == 'Taxon(id=137338523, full_name=Trachelipus rathkii (Rathke’s Woodlouse))'

    # Hyphens and parentheses in common name
    taxon_6 = Taxon(
        id=642466,
        name='Terpsiphone paradisi ceylonensis',
        preferred_common_name='Indian paradise-flycatcher (sri lanka)',
        rank='ssp',
    )
    assert str(taxon_6) == (
        'Taxon(id=642466, full_name=Terpsiphone paradisi ceylonensis (Indian Paradise-Flycatcher (Sri Lanka)))'
    )


def test_taxon__ancestors_children():
    taxon = Taxon.from_json(j_taxon_1)
    parent = taxon.ancestors[0]
    child = taxon.children[0]
    assert isinstance(parent, Taxon) and parent.id == 1
    assert isinstance(child, Taxon) and child.id == 70115


def test_taxon__ancestor_ids_from_ancestry_str():
    taxon = Taxon(ancestry='1/70116/70118')
    assert taxon.ancestor_ids == [1, 70116, 70118]


def test_taxon__ancestor_ids_from_ancestor_objs():
    ids = [1, 70116, 70118]
    taxon = Taxon(ancestors=[Taxon(id=i) for i in ids])
    assert taxon.ancestor_ids == ids


def test_taxon_ancestor_shortcuts():
    taxon = Taxon.from_json(j_taxon_1)
    assert taxon.kingdom.id == 1 and taxon.kingdom.name == 'Animalia'
    assert taxon.phylum.id == 47120 and taxon.phylum.name == 'Arthropoda'
    assert taxon.class_.id == 47158 and taxon.class_.name == 'Insecta'
    assert taxon.order.id == 47208 and taxon.order.name == 'Coleoptera'
    assert taxon.family.id == 53849 and taxon.family.name == 'Silphidae'
    assert taxon.genus.id == 53850 and taxon.genus.name == 'Nicrophorus'


def test_taxon__all_names():
    taxon = Taxon.from_json(j_taxon_8_all_names)
    assert taxon.names[1] == {
        'is_valid': True,
        'name': 'American Crow',
        'position': 0,
        'locale': 'en',
    }


def test_taxon__autocomplete():
    taxon = Taxon.from_json(j_taxon_7_autocomplete)
    assert taxon.matched_term == 'Vespidae'


def test_taxon__conservation_status():
    cs = Taxon.from_json(j_taxon_5_cs_status).conservation_status
    assert isinstance(cs, ConservationStatus)
    assert cs.status_name == 'imperiled'


def test_taxon__conservation_status_aliases():
    cs = Taxon.from_json(j_taxon_5_cs_status).conservation_status
    cs.user_id = 111
    cs.updater_id = 222
    cs.place_id = 333
    assert cs.user.id == cs.user_id == 111
    assert cs.updater.id == cs.updater_id == 222
    assert cs.place.id == cs.place_id == 333


def test_taxon__conservation_statuses():
    css = Taxon.from_json(j_taxon_6_cs_statuses).conservation_statuses[0]
    assert isinstance(css, ConservationStatus)
    assert css.status == 'EN'
    assert isinstance(css.updater, User) and css.user.id == 383144
    assert isinstance(css.user, User) and css.user.id == 383144


def test_taxon__establishment_means():
    es = Taxon.from_json(j_taxon_4_preferred_place).establishment_means
    assert isinstance(es, EstablishmentMeans)
    assert es.id == 5660131
    assert str(es) == 'EstablishmentMeans(introduced)'


def test_taxon__listed_taxa():
    taxon = Taxon.from_json(j_taxon_1)
    listed_taxon = taxon.listed_taxa[0]
    assert isinstance(listed_taxon, ListedTaxon)
    assert listed_taxon.taxon_id == taxon.id
    assert listed_taxon.list.id == 299
    assert listed_taxon.list.title == 'United States Check List'
    assert taxon.listed_taxa_count == 4
    assert str(listed_taxon) == (
        'ListedTaxon(id=5577060, taxon_id=70118, place=Place(id=1, location=(0, 0), '
        'name=United States), establishment_means=native, observations_count=0)'
    )


def test_listed_taxon__id_wrapper_properties():
    lt = ListedTaxon(list_id=299, place_id=1, user_id=2, updater_id=3)
    assert lt.list.id == lt.list_id == 299
    assert lt.place.id == lt.place_id == 1
    assert lt.user.id == lt.user_id == 2
    assert lt.updater.id == lt.updater_id == 3

    # Init with both list ID and object
    lt = ListedTaxon(list_id=299, list=Checklist(title='test checklist'))
    assert lt.list.id == 299
    assert lt.list.title == 'test checklist'


def test_taxon__properties():
    taxon = Taxon.from_json(j_taxon_1)
    taxon.gbif_id = 12345
    assert taxon.url == f'{INAT_BASE_URL}/taxa/70118'
    assert taxon.child_ids == [70115, 70114, 70117, 70116]
    assert taxon.gbif_url == f'{GBIF_TAXON_BASE_URL}/12345'
    assert isinstance(taxon.parent, Taxon) and taxon.parent.id == 53850


def test_taxon_properties__partial():
    taxon = Taxon.from_json(j_taxon_2_partial)
    assert taxon.parent is None


@pytest.mark.parametrize('taxon_id', ICONIC_TAXA.keys())
def test_taxon__emoji(taxon_id):
    taxon = Taxon(iconic_taxon_id=taxon_id)
    assert taxon.emoji is not None


@pytest.mark.parametrize('taxon_name', ICONIC_TAXA.values())
def test_taxon__icon_url(taxon_name):
    taxon = Taxon(iconic_taxon_name=taxon_name)
    assert taxon.icon_url is not None


@pytest.mark.parametrize('taxon_id', ICONIC_TAXA.keys())
def test_taxon__no_default_photo(taxon_id):
    taxon = Taxon(iconic_taxon_id=taxon_id)
    photo = taxon.default_photo
    assert isinstance(photo, IconPhoto)
    assert taxon.icon_url is not None
    assert taxon.iconic_taxon_name is not None
    assert photo.url is not None


def test_taxon__normalize_rank():
    taxon_1 = Taxon(rank='spp')
    taxon_2 = Taxon(rank='sPEciEs')
    assert taxon_1.rank == taxon_2.rank == 'species'


def test_taxon__rank_level():
    # If missing, level should be looked up by name, if available
    taxon = Taxon(rank='species')
    assert taxon.rank_level == 10

    # Otherwise, level should default to 'unranked' for comparison
    taxon = Taxon()
    assert taxon.rank_level == UNRANKED


def test_taxon__taxonomy():
    taxon = Taxon.from_json(j_taxon_1)
    assert taxon.taxonomy == {
        'kingdom': 'Animalia',
        'phylum': 'Arthropoda',
        'subphylum': 'Hexapoda',
        'class': 'Insecta',
        'subclass': 'Pterygota',
        'order': 'Coleoptera',
        'suborder': 'Polyphaga',
        'infraorder': 'Staphyliniformia',
        'superfamily': 'Staphylinoidea',
        'family': 'Silphidae',
        'subfamily': 'Nicrophorinae',
        'genus': 'Nicrophorus',
        'species': 'Nicrophorus vespilloides',
    }


def test_taxon_count__copy():
    """When an IconPhoto is used in place of a missing Taxon.default_photo, and the taxon is copied
    into a TaxonCount object, the IconPhoto object should be copied as-is instead of converting
    back to a dict and then into a Photo.
    """
    taxon = Taxon(id=1, iconic_taxon_id=3)
    taxon_counts = TaxonCount.copy(taxon)
    assert isinstance(taxon.default_photo, IconPhoto)
    assert isinstance(taxon_counts.default_photo, IconPhoto)
    assert taxon.default_photo.medium_url == taxon_counts.default_photo.medium_url


def test_taxon_counts__converters():
    taxon_counts = TaxonCounts.from_json(j_obs_species_counts)
    assert taxon_counts.data[0] == taxon_counts[0]
    assert len(taxon_counts) == 9
    assert isinstance(taxon_counts.data[0], TaxonCount) and taxon_counts.data[0].count == 31


def test_taxon_counts__empty():
    taxon_counts = TaxonCounts()
    assert taxon_counts.data == []
    assert taxon_counts.id_map == {}


def test_taxon_counts__slice():
    taxon_counts = TaxonCounts.from_json(j_obs_species_counts)
    sliced = taxon_counts[:3]
    assert len(sliced) == 3
    assert isinstance(sliced, TaxonCounts)
    assert all(isinstance(item, TaxonCount) for item in sliced)


def test_taxon_summary():
    ts = TaxonSummary.from_json(j_taxon_summary_2_listed)
    assert ts.listed_taxon.taxon_id == 47219
    assert ts.listed_taxon.place.id == 144952
    assert ts.listed_taxon.place.display_name.startswith('HRM District 13')
    assert ts.listed_taxon.place.place_type_name == 'Constituency'


# Taxon trees
# --------------------


def test_make_tree():
    root = make_tree(LifeList.from_json(j_life_list_2))

    # Spot check the first few levels
    assert root.name == 'Life'
    assert root.children[0].name == 'Animalia'
    assert root.children[0].children[0].name == 'Arthropoda'

    # Ensure correct child sort order
    node = root
    for _ in range(14):
        node = node.children[0]
    assert node.name == 'Bombus'
    children = [t.name for t in node.children]
    assert children == ['Bombus', 'Psithyrus', 'Pyrobombus', 'Subterraneobombus', 'Thoracobombus']
    assert (
        node.child_ids == [t.id for t in node.children] == [538903, 538893, 538900, 415027, 538902]
    )

    # Ensure ancestors are updated
    assert root.ancestors == []
    assert node.parent_id == 538883
    assert (
        node.ancestor_ids
        == [t.id for t in node.ancestors]
        == [
            48460,
            1,
            47120,
            372739,
            47158,
            184884,
            47201,
            124417,
            326777,
            47222,
            630955,
            47221,
            199939,
            538883,
        ]
    )


def test_make_tree__filtered():
    """Test a tree filtered by common ranks only"""
    root = make_tree(
        Taxon.from_json_list(j_life_list_2),
        include_ranks=COMMON_RANKS,
    )

    # Spot check the first few levels
    assert root.name == 'Animalia'
    assert root.children[0].children[0].name == 'Insecta'

    # 6 levels down, expect a genus with 9 species
    node = root
    for _ in range(5):
        node = node.children[0]
    assert node.name == 'Bombus'

    # We've skipped subgenus, so these should be in alphabetical order (not by subgenus then name)
    children = [t.name for t in node.children]
    assert children == [
        'Bombus bimaculatus',
        'Bombus borealis',
        'Bombus fervidus',
        'Bombus flavidus',
        'Bombus impatiens',
        'Bombus perplexus',
        'Bombus ternarius',
        'Bombus terricola',
        'Bombus vagans',
    ]


def test_make_tree__all_filtered():
    """When all available ranks are filtered out, a single root node should be created"""
    root = make_tree(
        Taxon.from_json_list(j_life_list_2),
        include_ranks=['infraclass'],
    )
    assert root.name == 'Life' and not root.children


def test_make_tree__preserves_originals():
    """Children/ancestors of original taxon objects should be preserved"""
    taxa = Taxon.from_json_list(j_life_list_2)
    animalia = taxa[1]
    animalia.ancestors = [Taxon(name='Life')]
    animalia.children = [Taxon(name='Arthropoda')]
    make_tree(taxa, include_ranks=['kingdom', 'class', 'family', 'genus', 'species'])

    assert animalia.ancestors[0].name == 'Life'
    assert animalia.children[0].name == 'Arthropoda'


def test_make_tree__find_root():
    """With 'Life' root node removed, the next highest rank should be used as root"""
    taxa = Taxon.from_json_list(j_life_list_2)[1:]
    root = make_tree(taxa)
    assert root.id == 1
    assert root.name == 'Animalia'


def test_make_tree__multiple_roots():
    """With 'Life' root node omitted by rank filter, but multiple kingdoms present, life needs to be
    added back to get a single root node
    """
    fungi = Taxon(id=47170, name='Fungi', rank='kingdom', parent_id=ROOT_TAXON_ID)
    taxa = Taxon.from_json_list(j_life_list_2) + [fungi]
    root = make_tree(taxa, include_ranks=COMMON_RANKS)
    assert root.id == ROOT_TAXON_ID
    assert root.name == 'Life'
    assert root.children[0].name == 'Animalia'
    assert root.children[1].name == 'Fungi'


def test_make_tree__ungrafted():
    """Additional ungrafted taxa should also be added under the 'Life' root node, regardless of rank"""
    monocots = Taxon(id=47163, name='Monocots', rank='class', parent_id=47125)
    taxa = Taxon.from_json_list(j_life_list_2) + [monocots]
    root = make_tree(taxa, include_ranks=COMMON_RANKS)
    assert root.id == ROOT_TAXON_ID
    assert root.name == 'Life'
    assert root.children[0].name == 'Animalia'
    assert root.children[1].name == 'Monocots'
    assert root.children[0].children[0].name == 'Arthropoda'


def test_make_tree__explicit_root():
    """If a root taxon is provided, it should be used as the root node if possible"""
    taxa = Taxon.from_json_list(j_life_list_2)
    root = make_tree(taxa, root_id=1)
    assert root.id == 1
    assert len(root.children) == 1
    assert root.children[0].name == 'Arthropoda'


def test_make_tree__explicit_root_not_found():
    """If a root taxon is provided but not included in the list, fall back to default behavior"""
    taxa = Taxon.from_json_list(j_life_list_2)
    root = make_tree(taxa, root_id=12345)
    assert root.id == ROOT_TAXON_ID
    assert len(root.children) == 1


def test_make_tree__explicit_root_filtered_out():
    """If a root taxon is provided, it should be exempt from rank filters"""
    taxa = Taxon.from_json_list(j_life_list_2)
    root = make_tree(taxa, root_id=1, include_ranks=['family', 'genus', 'species'])
    assert root.id == 1
    assert root.name == 'Animalia'
    assert len(root.children) == 1


def test_flatten():
    flat_list = make_tree(Taxon.from_json_list(j_life_list_1)).flatten()
    assert [t.id for t in flat_list] == [48460, 1, 2, 3, 573, 574, 889, 890, 980, 981]
    assert [t.indent_level for t in flat_list] == [0, 1, 2, 3, 4, 5, 6, 7, 6, 7]

    assert flat_list[0].ancestors == []
    assert [t.id for t in flat_list[5].ancestors] == [48460, 1, 2, 3, 573]
    assert [t.id for t in flat_list[9].ancestors] == [48460, 1, 2, 3, 573, 574, 980]


def test_flatten__filtered():
    flat_list = make_tree(
        Taxon.from_json_list(j_life_list_2),
        include_ranks=['kingdom', 'family', 'genus', 'subgenus'],
    ).flatten()
    assert [t.id for t in flat_list] == [
        1,
        47221,
        52775,
        538903,
        538893,
        538900,
        415027,
        538902,
    ]
    assert [t.indent_level for t in flat_list] == [0, 1, 2, 3, 3, 3, 3, 3]

    assert flat_list[0].ancestors == []
    assert [t.id for t in flat_list[1].ancestors] == [1]


def test_flatten__hide_root__noop():
    """hide_root with no automatically inserted root should have no effect"""
    taxa = Taxon.from_json_list(j_life_list_1)
    flat_list = make_tree(taxa).flatten(hide_root=True)
    assert [t.id for t in flat_list] == [48460, 1, 2, 3, 573, 574, 889, 890, 980, 981]
    assert [t.indent_level for t in flat_list] == [0, 1, 2, 3, 4, 5, 6, 7, 6, 7]


def test_flatten__hide_root__artificial():
    """hide_root with an automatically inserted root should remove root taxon"""
    taxa = Taxon.from_json_list(j_life_list_1)
    tree = make_tree(taxa)
    tree._artificial = True
    flat_list = tree.flatten(hide_root=True)
    assert [t.id for t in flat_list] == [1, 2, 3, 573, 574, 889, 890, 980, 981]
    assert [t.indent_level for t in flat_list] == [0, 1, 2, 3, 4, 5, 6, 5, 6]


def test_flatten__hide_root__multiple_roots():
    """hide_root with an automatically inserted root (due to multiple roots) should remove root taxon"""
    fungi = Taxon(id=47170, name='Fungi', rank='kingdom', parent_id=ROOT_TAXON_ID)
    taxa = Taxon.from_json_list(j_life_list_2) + [fungi]
    flat_list = make_tree(taxa, include_ranks=COMMON_RANKS).flatten(hide_root=True)
    assert [t.id for t in flat_list] == [
        1,
        47120,
        47158,
        47201,
        47221,
        52775,
        52779,
        143854,
        52774,
        541839,
        118970,
        155085,
        127905,
        121517,
        128670,
        47170,
    ]


# Users
# --------------------


def test_user__converters():
    user = User.from_json(j_user_1)
    assert user.identifications_count == 95624


def test_user__empty():
    user = User()
    assert isinstance(user.created_at, datetime)
    assert user.roles == []


def test_user__partial():
    user = User.from_json(j_user_2_partial)
    assert user.id == 886482
    assert user.name == 'Nicolas Noé'


def test_user__properties():
    user = User.from_json(j_user_1)
    assert user.username == user.login == 'kueda'
    assert user.display_name == user.name == 'Ken-ichi Ueda'


def test_user__str():
    user = User.from_json(j_user_1)
    assert str(user) == 'User(id=1, login=kueda, name=Ken-ichi Ueda)'


def test_user_count__str():
    user_count = UserCount.from_json(j_observation_identifiers['results'][0])
    assert str(user_count) == 'UserCount(id=112514, login=earthstephen, name=Stephen): 1'


def test_user_counts__identifiers():
    user_counts = UserCounts.from_json(j_observation_identifiers)
    assert user_counts.data[0] == user_counts[0]
    assert len(user_counts) == 3
    assert isinstance(user_counts.data[0], UserCount) and user_counts.data[0].count == 1


def test_user_counts__observers():
    user_counts = UserCounts.from_json(j_observation_observers)
    assert user_counts.data[0] == user_counts[0]
    assert len(user_counts) == 2
    assert isinstance(user_counts.data[0], UserCount) and user_counts.data[0].count == 750


def test_user_counts__empty():
    user_counts = UserCounts()
    assert user_counts.data == []
    assert user_counts.id_map == {}
