""" Data classes with utilities for managing specific resources """
# flake8: noqa: F401
# TODO: simplified __str__ implementations


# Imported in order of dependencies
from pyinaturalist.models.base import BaseModel, ModelCollection, aliased_kwarg, kwarg, timestamp
from pyinaturalist.models.photo import Photo, Photos
from pyinaturalist.models.taxon import Taxon, Taxa, get_icon_path
from pyinaturalist.models.user import User
from pyinaturalist.models.identification import Identification, Identifications
from pyinaturalist.models.observation import Observation, Observations
from pyinaturalist.models.image_metadata import ImageMetadata
from pyinaturalist.models.keyword_metadata import KeywordMetadata, KEYWORD_TAGS, HIER_KEYWORD_TAGS
from pyinaturalist.models.meta_metadata import MetaMetadata
