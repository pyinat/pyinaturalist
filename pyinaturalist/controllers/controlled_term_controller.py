from typing import Dict, List

from pyinaturalist.controllers import BaseController
from pyinaturalist.docs import document_controller_params
from pyinaturalist.models import Annotation, ControlledTerm
from pyinaturalist.v1 import get_controlled_terms, get_controlled_terms_for_taxon


class ControlledTermController(BaseController):
    """:fa:`tag` Controller for ControlledTerm and Annotation requests"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._term_lookup: Dict[int, ControlledTerm] = {}

    @property
    def term_lookup(self) -> Dict[int, ControlledTerm]:
        """Get a lookup table of controlled term IDs to term objects"""
        if not self._term_lookup:
            self._term_lookup = {term.id: term for term in self.all()}
        return self._term_lookup

    @document_controller_params(get_controlled_terms)
    def all(self, **params) -> List[ControlledTerm]:
        response = get_controlled_terms(**params)
        return ControlledTerm.from_json_list(response['results'])

    @document_controller_params(get_controlled_terms_for_taxon)
    def for_taxon(self, taxon_id: int, **params) -> List[ControlledTerm]:
        response = get_controlled_terms_for_taxon(taxon_id, **params)
        return ControlledTerm.from_json_list(response['results'])

    def lookup(self, annotations: List[Annotation]) -> List[Annotation]:
        """Fill in missing information for the specified annotations. If only term and value IDs are
        present, this will look up, cache, and add complete controlled term details.

        Args:
            annotations: Observation annotations

        Returns:
            Annotation objects with ``controlled_attribute`` and ``controlled_value`` populated
        """
        for annotation in annotations or []:
            term = self.term_lookup.get(annotation.controlled_attribute_id)
            if term:
                annotation.controlled_attribute = term
                annotation.controlled_value = term.get_value_by_id(annotation.controlled_value_id)
        return annotations
