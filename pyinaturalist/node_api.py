# Code to access the (read-only, but fast) Node based public iNaturalist API
# See: http://api.inaturalist.org/v1/docs/
from time import sleep

import requests
from requests.compat import urljoin

from inaturalist.constants import THROTTLING_DELAY, INAT_NODE_API_BASE_URL
from inaturalist.helpers import merge_two_dicts

PER_PAGE_RESULTS = 30  # Paginated queries: how many records do we ask per page?


def make_inaturalist_api_get_call(endpoint, params, **kwargs):
    """Make an API call to iNaturalist.

    endpoint is a string such as 'observations' !! do not put / in front
    method: 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'
    kwargs are passed to requests.request
    Returns a requests.Response object
    """
    headers = {'Accept': 'application/json'}

    return requests.get(urljoin(INAT_NODE_API_BASE_URL, endpoint), params, headers=headers, **kwargs)


def get_observations(params):
    """Search observations, see: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations.

    Returns the parsed JSON returned by iNaturalist (observations in r['results'], a list of dicts)
    """

    r = make_inaturalist_api_get_call('observations', params=params)
    return r.json()


def get_all_observations(params):
    """Like get_observations() but handles pagination so you get all the results in one shot.

    Some params will be overwritten: order_by, order, per_page, id_above (do NOT specify page when using this).

    Returns a list of dicts (one entry per observation)
    """

    # According to the doc: "The large size of the observations index prevents us from supporting the page parameter
    # when retrieving records from large result sets. If you need to retrieve large numbers of records, use the per_page
    # and id_above or id_below parameters instead.

    results = []
    id_above = 0

    while True:
        iteration_params = merge_two_dicts(params, {
            'order_by': 'id',
            'order': 'asc',
            'per_page': PER_PAGE_RESULTS,
            'id_above': id_above
        })

        page_obs = get_observations(params=iteration_params)
        results = results + page_obs['results']

        if page_obs['total_results'] <= PER_PAGE_RESULTS:
            return results

        sleep(THROTTLING_DELAY)
        id_above = results[-1]['id']