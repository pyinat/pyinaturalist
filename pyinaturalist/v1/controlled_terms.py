from typing import Optional

from pyinaturalist.constants import API_V1, JsonResponse
from pyinaturalist.exceptions import TaxonNotFound
from pyinaturalist.session import get


def get_controlled_terms(taxon_id: Optional[int] = None, **params) -> JsonResponse:
    """List controlled terms and their possible values

    .. rubric:: Notes

    * API reference: :v1:`GET /controlled_terms <Controlled_Terms/get_controlled_terms>`

    Example:
        >>> response = get_controlled_terms()
        >>> pprint(response)
        1: Life Stage
            2: Adult
            3: Teneral
            4: Pupa
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms.json
                :language: JSON
    Returns:
        A dict containing details on controlled terms and their values
    """
    # For backwards-compatibility
    if taxon_id:
        return get_controlled_terms_for_taxon(taxon_id, **params)

    response = get(f'{API_V1}/controlled_terms', **params)
    return response.json()


def get_controlled_terms_for_taxon(taxon_id: int, **params) -> JsonResponse:
    """List controlled terms that are valid for the specified taxon.

    .. rubric:: Notes

    * API reference: :v1:`GET /controlled_terms/for_taxon <Controlled_Terms/get_controlled_terms_for_taxon>`

    Example:
        >>> response = get_controlled_terms_for_taxon(12345)
        >>> pprint(response)
        1: Life Stage
            2: Adult
            3: Teneral
            4: Pupa
        ...

        .. admonition:: Example Response
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms_for_taxon.json
                :language: JSON
    Args:
        taxon_id: ID of taxon to get controlled terms for

    Returns:
        A dict containing details on controlled terms and their values

    Raises:
        :py:exc:`.TaxonNotFound`: If an invalid ``taxon_id`` is specified
    """
    response = get(f'{API_V1}/controlled_terms/for_taxon', taxon_id=taxon_id, **params)

    # This endpoint returns a 422 if the specified taxon does not exist
    if response.status_code in (404, 422):
        raise TaxonNotFound
    return response.json()
