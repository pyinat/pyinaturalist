from requests import HTTPError


class AuthenticationError(HTTPError):
    pass


class ObservationNotFound(HTTPError):
    pass
