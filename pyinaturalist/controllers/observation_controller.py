from collections.abc import Callable
from inspect import signature
from logging import getLogger
from typing import Any

from pyinaturalist.constants import (
    API_V1,
    MAX_IDS_PER_REQUEST,
    V1_OBS_ORDER_BY_PROPERTIES,
    IntOrStr,
    MultiFile,
    MultiInt,
    MultiIntOrStr,
)
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.docs import copy_doc_signature
from pyinaturalist.docs import templates as docs
from pyinaturalist.models import (
    Annotation,
    ControlledTermCounts,
    Histogram,
    LifeList,
    Observation,
    Photo,
    Sound,
    TaxonCounts,
    TaxonSummary,
    UserCounts,
)
from pyinaturalist.paginator import IDPaginator, IDRangePaginator, Paginator
from pyinaturalist.request_params import validate_multiple_choice_param
from pyinaturalist.v1 import (
    create_observation,
    delete_observation,
    get_life_list_metadata,
    get_observation_identifiers,
    get_observation_observers,
    get_observation_popular_field_values,
    get_observation_species_counts,
    get_observation_taxon_summary,
    get_observation_taxonomy,
    update_observation,
    upload,
)

logger = getLogger(__name__)

_OBSERVATION_MUTABLE_PARAMS = {
    *signature(docs._create_observation).parameters,
    *signature(docs._create_observation_v2).parameters,
    *signature(docs._update_observation).parameters,
}
_OBSERVATION_ATTR_ALIASES = {
    'captive': 'captive_flag',
    'license_code': 'license',
    'tags': 'tag_list',
}


class ObservationController(BaseController):
    """:fa:`binoculars` Controller for Observation requests"""

    def __call__(self, observation_id: int, **params) -> Observation | None:
        """Get a single observation by ID

        Example:
            >>> client.observations(16227955)

        Args:
            observation_id: A single observation ID
        """
        return self.from_ids(observation_id, **params).one()

    def from_ids(self, observation_ids: MultiInt, **params) -> Paginator[Observation]:
        """Get one or more observations by ID

        .. rubric:: Notes

        * :fas:`lock-open` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
        * API reference: :v1:`GET /observations/{id} <Observations/get_observations_id>`

        Examples:
            >>> obs = client.observations.from_ids(16227955).all()
            >>> obs = client.observations.from_ids([16227955, 16227956]).all()

        Args:
            observation_ids: One or more observation IDs
        """

        def get_observations_by_id(_observation_ids: MultiInt, **params):
            return self.client.session.request(
                'GET', f'{API_V1}/observations', ids=_observation_ids, **params
            ).json()

        params = self.client.add_defaults(get_observations_by_id, params)

        return IDPaginator(
            get_observations_by_id,
            Observation,
            ids=ensure_list(observation_ids),
            ids_per_request=MAX_IDS_PER_REQUEST,
            **params,
        )

    @copy_doc_signature(*docs._get_observations, docs._only_id)
    def search(self, **params) -> Paginator[Observation]:
        """Search observations

        .. rubric:: Notes

        * :fas:`lock-open` :ref:`Optional authentication <auth>` (For private/obscured coordinates)
        * API reference: :v1:`GET /observations <Observations/get_observations>`

        Examples:

            Get observations of Monarch butterflies with photos + public location info,
            on a specific date in the province of Saskatchewan, CA (place ID 7953):

            >>> query = client.observations.search(
            >>>     taxon_name='Danaus plexippus',
            >>>     created_on='2020-08-27',
            >>>     photos=True,
            >>>     geo=True,
            >>>     geoprivacy='open',
            >>>     place_id=7953,
            >>> )
            >>> observations = query.all()

            Get basic info for observations in response:

            >>> pprint(observations)
            ID       Taxon ID Taxon                       Observed on   User      Location
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            57707611 48662    Danaus plexippus (Monarch)  Aug 26, 2020  ingridt3  Michener Dr, Regina, SK, CA
            57754375 48662    Danaus plexippus (Monarch)  Aug 27, 2020  samroom   Railway Ave, Wilcox, SK, CA

            Search for observations with a given observation field:

            >>> obs = client.observations.search(observation_fields=['Species count']).all()

            Or observation field value:

            >>> obs = client.observations.search(observation_fields={'Species count': 2}).all()

        """

        def get_observations(**params):
            return self.client.session.get(f'{API_V1}/observations', **params).json()

        params = validate_multiple_choice_param(params, 'order_by', V1_OBS_ORDER_BY_PROPERTIES)
        params = self.client.add_defaults(get_observations, params)

        return ObservationPaginator(
            get_observations,
            Observation,
            loop=self.client.loop,
            annotation_callback=self.client.annotations.lookup,
            **params,
        )

    @copy_doc_signature(*docs._get_observations, docs._observation_histogram)
    def histogram(self, **params) -> Histogram:
        """Search observations and return histogram data for the given time interval

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/histogram <Observations/get_observations_histogram>`
        * Search parameters are the same as :py:func:`~pyinaturalist.v1.observations.get_observations()`,
          with the addition of ``date_field`` and ``interval``.
        * ``date_field`` may be either 'observed' (default) or 'created'.
        * Observed date ranges can be filtered by parameters ``d1`` and ``d2``
        * Created date ranges can be filtered by parameters ``created_d1`` and ``created_d2``
        * ``interval`` may be one of: 'year', 'month', 'week', 'day', 'hour', 'month_of_year', or
          'week_of_year'; spaces are also allowed instead of underscores, e.g. 'month of year'.
        * The year, month, week, day, and hour interval options will set default values for ``d1`` and
          ``created_d1``, to limit the number of groups returned. You can override those values if you
          want data from a longer or shorter time span.
        * The 'hour' interval only works with ``date_field='created'``

        Example:
            Get observations per month during the first half of 2020 in Austria (place ID 8057)

            >>> hist = client.observations.histogram(
            >>>     interval='month',
            >>>     d1='2020-01-01',
            >>>     d2='2020-06-30',
            >>>     place_id=8057,
            >>> )
            >>> pprint(hist)
            Month     Count
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            2020-01   2565    ████
            2020-02   3218    ██████
            2020-03   8150    ███████████████
            2020-04   26438   ██████████████████████████████████████████████████
            2020-05   23656   ████████████████████████████████████████████
            2020-06   23862   █████████████████████████████████████████████

            .. dropdown:: Example Response (observations per month of year)
                :color: primary
                :icon: code-square

                >>> hist.raw

                .. literalinclude:: ../sample_data/v1/get_observation_histogram_month_of_year.py

            .. dropdown:: Example Response (observations per month)
                :color: primary
                :icon: code-square

                >>> hist.raw

                .. literalinclude:: ../sample_data/v1/get_observation_histogram_month.py
                    :lines: 3-

            .. dropdown:: Example Response (observations per day)
                :color: primary
                :icon: code-square

                >>> hist.raw

                .. literalinclude:: ../sample_data/v1/get_observation_histogram_day.py
                    :lines: 3-

        """
        response = self.client.session.get(f'{API_V1}/observations/histogram', **params).json()
        return Histogram.from_json(response['results'])

    # TODO: Example response UserCounts object?
    @copy_doc_signature(*docs._get_observations)
    def identifiers(self, **params) -> UserCounts:
        """Get identifiers of observations matching the search criteria and the count of
        observations they have identified. By default, results are sorted by ID count in descending.

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/identifiers <Observations/get_observations_identifiers>`
        * This endpoint will only return up to 500 results.

        Example:
            >>> client.observations.identifiers(place_id=72645)
        """
        response = self.client.request(get_observation_identifiers, **params)
        return UserCounts.from_json(response)

    def life_list(
        self, user_id: IntOrStr | None = None, locale: str | None = None, **params
    ) -> LifeList:
        """Get taxa from a user's dynamic life list

        .. rubric:: Notes

        * Results are returned in a flat list, but are ordered as they would be in a taxonomic tree

        Args:
            user_id: iNaturalist user ID or username
            locale: Locale preference for taxon common names
        """
        response = self.client.request(get_observation_taxonomy, user_id=user_id, **params)

        # Add additional metadata to a life list response; requires a user ID
        if user_id:
            metadata = self.client.request(
                get_life_list_metadata, user_id=user_id, locale=locale, **params
            )
            meta_by_id = {item['id']: item for item in metadata['results']}
            for taxon in response['results']:
                taxon.update(meta_by_id.get(taxon['id'], {}))

        return LifeList.from_json(response)

    # TODO: Example response UserCounts object?
    @copy_doc_signature(*docs._get_observations)
    def observers(self, **params) -> UserCounts:
        """Get observers of observations matching the search criteria and the count of
        observations and distinct taxa of rank species they have observed.

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/observers <Observations/get_observations_observers>`
        * Options for ``order_by`` are 'observation_count' (default) or 'species_count'
        * This endpoint will only return up to 500 results
        * See this issue for more details: https://github.com/inaturalist/iNaturalistAPI/issues/235

        Example:
            >>> client.observations.observers(place_id=72645, order_by='species_count')
        """
        response = self.client.request(get_observation_observers, **params)
        return UserCounts.from_json(response)

    @copy_doc_signature(*docs._get_observations)
    def popular_fields(self, **params) -> ControlledTermCounts:
        """Get controlled terms values and a monthly histogram of observations matching the search
        criteria.

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/popular_field_values
          <Observations/get_observations_popular_field_values>`

        Example:
            >>> client.observations.popular_fields(species_name='Danaus plexippus', place_id=24)
        """
        response = self.client.request(get_observation_popular_field_values, **params)
        return ControlledTermCounts.from_json(response)

    @copy_doc_signature(*docs._get_observations)
    def species_count(self, **params) -> int:
        """Get a total count of species (or other 'leaf taxa') associated with observations matching the search
        criteria.

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/species_counts <Observations/get_observations_species_counts>`
        * **Leaf taxa** are the leaves of the taxonomic tree, like species, subspecies, variety, or form
        * This method returns only the combined total number of leaf taxa in matched observations;
          :py:meth:`.species_counts` returns the full list of taxa and the number of observations for each

        Example:
            >>> client.observations.species_count(taxon_id=52775, place_id=6853)
        """
        response = self.client.request(get_observation_species_counts, count_only=True, **params)
        return response['total_results']

    @copy_doc_signature(*docs._get_observations)
    def species_counts(self, **params) -> TaxonCounts:
        """Get all species (or other 'leaf taxa') associated with observations matching the search
        criteria, and the count of observations they are associated with.

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/species_counts <Observations/get_observations_species_counts>`
        * **Leaf taxa** are the leaves of the taxonomic tree, like species, subspecies, variety, or form

        Example:
            >>> client.observations.species_counts(user_login='my_username', quality_grade='research')
        """
        response = self.client.request(get_observation_species_counts, **params)
        return TaxonCounts.from_json(response)

    def taxon_summary(self, observation_id: int, **params) -> TaxonSummary:
        """Get information about an observation's taxon, within the context of the observation's location

        .. rubric:: Notes

        * API reference: :v1:`GET /observations/{id}/taxon_summary <Observations/get_observations_id_taxon_summary>`

        Args:
            observation_id: Observation ID to get taxon summary for

        Example:
            >>> client.observations.taxon_summary(7849808)
        """
        response = self.client.request(
            get_observation_taxon_summary, observation_id=observation_id, **params
        )
        return TaxonSummary.from_json(response)

    @staticmethod
    def _has_value(value: Any) -> bool:
        return value not in (None, '', [], {}, ())

    @staticmethod
    def _extract_id(value: Any) -> int | None:
        if isinstance(value, dict):
            return value.get('id')
        return getattr(value, 'id', None)

    @classmethod
    def _observation_to_params(cls, observation: Observation) -> tuple[dict[str, Any], list[str]]:
        params: dict[str, Any] = {}
        ignored_attrs: set[str] = set()
        obs_dict = observation.to_dict()

        for key, value in obs_dict.items():
            if not cls._has_value(value):
                continue

            if key == 'location':
                coords = ensure_list(value)
                if len(coords) == 2 and cls._has_value(coords[0]) and cls._has_value(coords[1]):
                    lat, lng = coords
                    params['latitude'] = lat
                    params['longitude'] = lng
                else:
                    ignored_attrs.add(key)
                continue

            if key == 'taxon':
                if taxon_id := cls._extract_id(value):
                    params['taxon_id'] = taxon_id
                else:
                    ignored_attrs.add(key)
                continue

            if key == 'ofvs':
                ofv_params = {}
                for ofv in ensure_list(value):
                    field_id = (
                        (ofv.get('observation_field_id') if isinstance(ofv, dict) else None)
                        or cls._extract_id(ofv.get('observation_field') if isinstance(ofv, dict) else None)
                        or getattr(ofv, 'observation_field_id', None)
                    )
                    field_value = ofv.get('value') if isinstance(ofv, dict) else getattr(ofv, 'value', None)
                    if cls._has_value(field_id) and cls._has_value(field_value):
                        ofv_params[field_id] = field_value

                if ofv_params:
                    params['observation_fields'] = ofv_params
                else:
                    ignored_attrs.add(key)
                continue

            if key == 'photos':
                photo_ids = [photo_id for p in ensure_list(value) if (photo_id := cls._extract_id(p))]
                if photo_ids:
                    params['photo_ids'] = photo_ids
                else:
                    ignored_attrs.add(key)
                continue

            param_key = _OBSERVATION_ATTR_ALIASES.get(key, key)
            if param_key in _OBSERVATION_MUTABLE_PARAMS:
                params[param_key] = value
            else:
                ignored_attrs.add(key)

        return params, sorted(ignored_attrs)

    @classmethod
    def _merge_observation_params(
        cls,
        observation: Observation | None,
        params: dict[str, Any],
        require_observation_id: bool = False,
    ) -> dict[str, Any]:
        if observation and not isinstance(observation, Observation):
            raise TypeError(f'Expected Observation object; got: {type(observation).__name__}')

        if not observation:
            if require_observation_id and not params.get('observation_id'):
                raise ValueError(
                    'Must provide observation_id or pass an Observation object with a valid ID'
                )
            return params

        obs_params, ignored_attrs = cls._observation_to_params(observation)
        merged_params = {**obs_params, **params}

        if require_observation_id and not merged_params.get('observation_id'):
            if observation.id:
                merged_params['observation_id'] = observation.id
            else:
                raise ValueError(
                    'Must provide observation_id or pass an Observation object with a valid ID'
                )

        if ignored_attrs:
            logger.warning(
                f'Read-only observation attributes ignored: {", ".join(ignored_attrs)}'
            )
        return merged_params

    @copy_doc_signature(docs._observation_object, docs._create_observation)
    def create(self, observation: Observation | None = None, **params) -> Observation:
        """Create or update an observation.

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`POST /observations <Observations/post_observations>`

        Example:
            >>> client.observations.create(
            ...     species_guess='Pieris rapae',
            ...     photos='~/observation_photos/2020_09_01_14003156.jpg',
            ...     observation_fields={297: 1},  # 297 is the obs. field ID for 'Number of individuals'
            ... )
        """
        params = self._merge_observation_params(observation, params)
        response = self.client.request(create_observation, auth=True, **params)
        return Observation.from_json(response)

    def delete(self, observation_ids: MultiInt, **params):
        """Delete one or more observations

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`DELETE /observations/{id} <Observations/delete_observations_id>`


        Example:
            >>> delete_observation(17932425, token)

        Args:
            observation_ids: One or more observation IDs
        """
        for observation_id in ensure_list(observation_ids):
            self.client.request(
                delete_observation,
                auth=True,
                observation_id=observation_id,
                **params,
            )

    @copy_doc_signature(docs._observation_id, docs._observation_object, docs._create_observation)
    def update(self, observation: Observation | None = None, **params) -> Observation:
        """Update a single observation

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`PUT /observations <Observations/put_observations>`

        Example:
            >>> client.observations.update(
            >>>     observation_id=17932425,
            >>>     description='updated description!',
            >>> )
        """
        params = self._merge_observation_params(observation, params, require_observation_id=True)
        params = self.client.add_defaults(update_observation, params, auth=True)
        response = update_observation(**params)
        return Observation.from_json(response)

    def upload(
        self,
        observation_id: int,
        photos: MultiFile | None = None,
        sounds: MultiFile | None = None,
        photo_ids: MultiIntOrStr | None = None,
        **params,
    ) -> list[Photo | Sound]:
        """Upload one or more local photo and/or sound files, and add them to an existing observation.

        You may also attach a previously uploaded photo by photo ID, e.g. if your photo contains
        multiple organisms and you want to create a separate observation for each one.

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`POST /observation_photos <Observation_Photos/post_observation_photos>`

        Example:

            >>> client.observations.upload(
            ...     1234,
            ...     photos=['~/observations/2020_09_01_140031.jpg', '~/observations/2020_09_01_140042.jpg'],
            ...     sounds='~/observations/2020_09_01_140031.mp3',
            ...     photo_ids=[1234, 5678],
            ... )

            .. dropdown:: Example Response
                :color: primary
                :icon: code-square

                .. literalinclude:: ../sample_data/v1/upload_photos_and_sounds.json
                    :language: JSON

        Args:
            observation_id: the ID of the observation
            photos: One or more image files, file-like objects, file paths, or URLs
            sounds: One or more audio files, file-like objects, file paths, or URLs
            photo_ids: One or more IDs of previously uploaded photos to attach to the observation
            access_token: Access token for user authentication, as returned by :func:`get_access_token()`

        Returns:
            :py:class:`.Photo` or :py:class:`.Sound` objects for each uploaded file
        """
        responses = self.client.request(
            upload,
            auth=True,
            observation_id=observation_id,
            photos=photos,
            sounds=sounds,
            photo_ids=photo_ids,
            **params,
        )
        response_objs: list[Photo | Sound] = []
        for response in responses:
            if 'photo' in response:
                response_objs.append(Photo.from_json(response))
            elif 'sound' in response:
                response_objs.append(Sound.from_json(response))
        return response_objs


class ObservationPaginator(IDRangePaginator):
    """Paginate through observation results by a range of IDs instead of standard pagination
    parameters

    This also optionally fills in missing annotation information for each observation, using results
    from ``GET /controlled_terms``.
    """

    def __init__(
        self,
        *args,
        annotation_callback: Callable[[list[Annotation]], list[Annotation]],
        order: str = 'asc',
        **kwargs,
    ):
        super().__init__(*args, order=order, **kwargs)
        self.annotation_callback = annotation_callback

    def next_page(self) -> list[Observation]:
        observations = super().next_page()
        # Use cached controlled_terms lookup to fill in missing annotation details
        for obs in observations:
            obs.annotations = self.annotation_callback(obs.annotations)
        return observations
