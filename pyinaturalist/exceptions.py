# TODO: Make these extend `requests.HTTPError` to simplify error handling in client code?
class AuthenticationError(Exception):
    pass


class ObservationNotFound(Exception):
    pass
