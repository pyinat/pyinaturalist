"""Tests for backwards-compatible (but deprecated) imports"""
# flake8: noqa: F401


def test_v0_imports():

    from pyinaturalist.rest_api import (
        add_photo_to_observation,
        create_observation,
        delete_observation,
        get_all_observation_fields,
        get_observation_fields,
        get_observations,
        put_observation_field_values,
        update_observation,
        upload_photos,
    )


def test_v1_imports():
    from pyinaturalist.node_api import (
        get_controlled_terms,
        get_identifications,
        get_identifications_by_id,
        get_observation,
        get_observation_histogram,
        get_observation_identifiers,
        get_observation_observers,
        get_observation_species_counts,
        get_observations,
        get_places_autocomplete,
        get_places_by_id,
        get_places_nearby,
        get_projects,
        get_projects_by_id,
        get_taxa,
        get_taxa_autocomplete,
        get_taxa_by_id,
        get_user_by_id,
        get_users_autocomplete,
        search,
    )
