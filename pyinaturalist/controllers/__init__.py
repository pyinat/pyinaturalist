"""Controller classes for :py:class:`.iNatClient`. These contain all the request functions used by
the client, grouped by resource type.
"""

# ruff: noqa: F401
# isort: skip_file
from pyinaturalist.controllers.base_controller import BaseController
from pyinaturalist.controllers.annotation_controller import AnnotationController
from pyinaturalist.controllers.identification_controller import IdentificationController
from pyinaturalist.controllers.observation_controller import ObservationController
from pyinaturalist.controllers.observation_field_controller import ObservationFieldController
from pyinaturalist.controllers.place_controller import PlaceController
from pyinaturalist.controllers.project_controller import ProjectController
from pyinaturalist.controllers.taxon_controller import TaxonController
from pyinaturalist.controllers.user_controller import UserController
from pyinaturalist.controllers.search_controller import SearchController
