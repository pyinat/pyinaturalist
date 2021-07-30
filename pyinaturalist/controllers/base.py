class BaseController:
    """Base class for resource-specific controllers"""

    def __init__(self, client):
        self.client = client
