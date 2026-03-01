from logging import getLogger

from pyinaturalist.constants import API_V2, IntOrStr
from pyinaturalist.controllers import BaseController
from pyinaturalist.models import Annotation, ControlledTerm
from pyinaturalist.session import delete, post
from pyinaturalist.v1 import get_controlled_terms, get_controlled_terms_for_taxon

logger = getLogger(__name__)


class AnnotationController(BaseController):
    """:fa:`tag` Controller for Annotation and ControlledTerm requests"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._term_lookup: dict[int, ControlledTerm] = {}

    @property
    def term_lookup(self) -> dict[int, ControlledTerm]:
        """Get a lookup table of controlled term IDs to term objects"""
        if not self._term_lookup:
            self._term_lookup = {term.id: term for term in self.all()}
        return self._term_lookup

    def all(self, **params) -> list[ControlledTerm]:
        """List controlled terms and their possible values

        .. rubric:: Notes

        * API reference: :v1:`GET /controlled_terms <Controlled_Terms/get_controlled_terms>`

        Example:
            >>> terms = client.annotations.all()
            >>> pprint(terms)
             ID   Label          Values
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             1    Life Stage     Adult, Teneral, Pupa, ...
             17   Alive or Dead  Alive, Dead, Cannot Be Determined
             ...

        """
        response = get_controlled_terms(**params)
        return ControlledTerm.from_json_list(response['results'])

    def for_taxon(self, taxon_id: int, **params) -> list[ControlledTerm]:
        """List controlled terms that are valid for the specified taxon.

        .. rubric:: Notes

        * API reference: :v1:`GET /controlled_terms/for_taxon <Controlled_Terms/get_controlled_terms_for_taxon>`

        Example:
            >>> client.annotations.for_taxon(12345)

        Args:
            taxon_id: Taxon ID to get controlled terms for

        Raises:
            :py:exc:`.TaxonNotFound`: If an invalid ``taxon_id`` is specified
        """
        response = get_controlled_terms_for_taxon(taxon_id, **params)
        return ControlledTerm.from_json_list(response['results'])

    def lookup(self, annotations: list[Annotation]) -> list[Annotation]:
        """Fill in missing information for the specified annotations. If only term and value IDs are
        present, this will look up, cache, and add complete controlled term details.

        Args:
            annotations: Observation annotations

        Returns:
            Annotation objects with ``controlled_attribute`` and ``controlled_value`` populated
        """
        for annotation in annotations or []:
            term = self.term_lookup.get(annotation.controlled_attribute.id)
            if term:
                annotation.controlled_attribute = term
                annotation.controlled_value = term.get_value_by_id(annotation.controlled_value.id)
            else:
                logger.warning(
                    f'No controlled attribute found for ID: {annotation.controlled_attribute.id}'
                )
        return annotations

    def _resolve_annotation_ids(
        self,
        controlled_attribute_id: int | None,
        controlled_value_id: int | None,
        term: str | None,
        value: str | None,
    ) -> tuple[int, int]:
        if controlled_attribute_id is not None and controlled_value_id is not None:
            return controlled_attribute_id, controlled_value_id

        # Resolve term + value labels to IDs
        if term is not None and value is not None:
            controlled_term = ControlledTerm.get_term_by_label(self.term_lookup.values(), term)
            if not controlled_term:
                raise ValueError(f'Annotation term not found: "{term}"')

            controlled_value = controlled_term.get_value_by_label(value)
            if not controlled_value:
                raise ValueError(
                    f'Annotation value not found for term "{controlled_term.label}": "{value}"'
                )

            return controlled_term.id, controlled_value.id

        raise ValueError(
            'Must specify either controlled_attribute_id + controlled_value_id or term + value'
        )

    def create(
        self,
        resource_id: IntOrStr,
        controlled_attribute_id: int | None = None,
        controlled_value_id: int | None = None,
        resource_type: str = 'Observation',
        term: str | None = None,
        value: str | None = None,
        **params,
    ) -> Annotation:
        """Create a new annotation on an observation.

        Args:
            resource_id: Observation ID or UUID
            controlled_attribute_id: Annotation attribute ID
            controlled_value_id: Annotation value ID
            resource_type: Resource type, if something other than an observation
            term: Annotation term label, used as an alternative to ``controlled_attribute_id``
            value: Annotation value label, used as an alternative to ``controlled_value_id``

        Example:
            Add a 'Plant phenology: Flowering' annotation to an observation (via IDs):

            >>> client.annotations.create(
            ...     164609837,
            ...     controlled_attribute_id=12,
            ...     controlled_value_id=13,
            ... )

            Add the same annotation by label:

            >>> client.annotations.create(164609837, term='Plant Phenology', value='Flowering')

        Returns:
            The newly created Annotation object
        """
        controlled_attribute_id, controlled_value_id = self._resolve_annotation_ids(
            controlled_attribute_id,
            controlled_value_id,
            term,
            value,
        )

        response = post(
            f'{API_V2}/annotations',
            controlled_attribute_id=controlled_attribute_id,
            controlled_value_id=controlled_value_id,
            resource_id=resource_id,
            resource_type=resource_type,
            **params,
        )
        return Annotation.from_json(response.json()['results'][0])

    def delete(self, uuid: str, **params):
        """Delete an annotation

        Args:
            uuid: Annotation UUID

        Returns:
            Nothing; success means the item has been deleted
        """
        delete(f'{API_V2}/annotations/{uuid}', **params)
