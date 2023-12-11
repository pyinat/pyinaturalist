from typing import Optional

from pyinaturalist.constants import IntOrStr, MultiIntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.converters import ensure_list
from pyinaturalist.models import User
from pyinaturalist.paginator import IDPaginator, Paginator
from pyinaturalist.v1 import get_current_user, get_user_by_id, get_users_autocomplete


class UserController(BaseController):
    """:fa:`user` Controller for User requests"""

    def __call__(self, user_id: IntOrStr, **kwargs) -> Optional[User]:
        """Get a single user by ID

        Example:
            >>> user = client.users(1)

        Args:
            user_id: A single user ID
        """
        return self.from_ids(user_id, **kwargs).one()

    def from_ids(self, user_ids: MultiIntOrStr, **params) -> Paginator[User]:
        """Get users by ID

        Example:
            Get a user by ID:

            >>> user = client.users.from_id(1).one()

            Get multiple users by ID:

            >>> users = client.users.from_id([1,2]).all()

        Args:
            user_ids: One or more user IDs
        """
        return self.client.paginate(
            get_user_by_id, User, cls=IDPaginator, ids=ensure_list(user_ids), **params
        )

    def autocomplete(
        self, q: Optional[str] = None, project_id: Optional[int] = None, **params
    ) -> Paginator[User]:
        """Given a query string, return users with names or logins starting with the search term

        .. rubric:: Notes

        * API reference: :v1:`GET /users/autocomplete <Users/get_users_autocomplete>`

        Example:
            >>> client.users.autocomplete(q='my_userna')

        Args:
            q: Search query
            project_id: Only show users who are members of this project
        """
        return self.client.paginate(
            get_users_autocomplete, User, q=q, project_id=project_id, **params
        )

    def me(self, **params) -> User:
        """Get your own user profile

        .. rubric:: Notes

        * :fa:`lock` :ref:`Requires authentication <auth>`
        * API reference: :v1:`GET /users/me <Users/get_users_me>`

        Example:
            >>> client.users.me()
        """
        response = self.client.request(get_current_user, auth=True, **params)
        return User.from_json(response)
