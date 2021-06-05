from pyinaturalist.constants import JsonResponse
from pyinaturalist.exceptions import TaxonNotFound
from pyinaturalist.v1 import get_v1


def get_controlled_terms(taxon_id: int = None, user_agent: str = None) -> JsonResponse:
    """List controlled terms and their possible values.
    A taxon ID can optionally be provided to show only terms that are valid for that taxon.
    Otherwise, all controlled terms will be returned.

    **API reference:**

    * https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms
    * https://api.inaturalist.org/v1/docs/#!/Controlled_Terms/get_controlled_terms_for_taxon

    Example:

        >>> response = get_controlled_terms()
        >>> print(format_controlled_terms(response))
        1: Life Stage
            2: Adult
            3: Teneral
            4: Pupa
        ...

        .. admonition:: Example Response (all terms)
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms.json
                :language: JSON

        .. admonition:: Example Response (for a specific taxon)
            :class: toggle

            .. literalinclude:: ../sample_data/get_controlled_terms_for_taxon.json
                :language: JSON
    Args:
        taxon_id: ID of taxon to get controlled terms for
        user_agent: a user-agent string that will be passed to iNaturalist.

    Returns:
        A dict containing details on controlled terms and their values

    Raises:
        :py:exc:`.TaxonNotFound` If an invalid taxon_id is specified
    """
    # This is actually two endpoints, but they are so similar it seems best to combine them
    endpoint = 'controlled_terms/for_taxon' if taxon_id else 'controlled_terms'
    response = get_v1(endpoint, params={'taxon_id': taxon_id}, user_agent=user_agent)

    # controlled_terms/for_taxon returns a 422 if the specified taxon does not exist
    if response.status_code in (404, 422):
        raise TaxonNotFound
    return response.json()
