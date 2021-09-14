from typing import Iterator, List

from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import User
from pyinaturalist.v1 import get_user_by_id, get_users_autocomplete


class UserController(BaseController):
    """:fa:`user` Controller for User requests"""

    # TODO: Paginator subclass for this?
    # TODO: Easier usage if you just want one result
    def from_id(self, *user_ids, **params) -> Iterator[User]:
        """Get users by ID

        Args:
            user_ids: One or more project IDs
        """
        for user_id in user_ids:
            response = get_user_by_id(user_id, **params)
            yield User.from_json(response)

    @document_controller_params(get_users_autocomplete)
    def autocomplete(self, **params) -> List[User]:
        response = get_users_autocomplete(**params)
        return User.from_json_list(response)
