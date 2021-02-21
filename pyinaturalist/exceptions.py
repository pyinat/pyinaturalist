from requests import HTTPError


class AuthenticationError(HTTPError):
    pass


class ObservationNotFound(HTTPError):
    pass


class TaxonNotFound(HTTPError):
    pass


class TooManyRequests(HTTPError):
    """Error raised for either a 429 response, or pre-emptively before we reach the rate limit"""
