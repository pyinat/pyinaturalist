.. _endpoints:

Endpoint Summary
================
Below is a list of iNaturalist API endpoints that have either been added or may be added in the
future, along with their corresponding functions in pyinaturalist.

v1 API
~~~~~~
For all available endpoints, see: http://api.inaturalist.org/v1/docs/

========= ======================================= ====================
Method    Endpoint                                Function
========= ======================================= ====================
POST      /annotations
DELETE    /annotations/{id}
POST      /comments
DELETE    /comments/{id}
PUT       /comments/{id}
GET       /controlled_terms                       :py:func:`.get_controlled_terms`
GET       /controlled_terms/for_taxon             :py:func:`.get_controlled_terms`
GET       /identifications                        :py:func:`.get_identifications`
GET       /identifications/{id}                   :py:func:`.get_identifications_by_id`
POST      /identifications
GET       /identifications/categories
GET       /identifications/species_counts
GET       /identifications/identifiers
GET       /identifications/observers
GET       /identifications/recent_taxa
GET       /identifications/similar_species
GET       /messages
POST      /messages
DELETE    /messages/{id}
GET       /messages/{id}
GET       /messages/unread
DELETE    /observation_field_values/{id}
PUT       /observation_field_values/{id}
POST      /observation_field_values
DELETE    /observation_photos/{id}
PUT       /observation_photos/{id}
POST      /observation_photos
DELETE    /observations/{id}
GET       /observations/{id}                      :py:func:`.get_observation`
PUT       /observations/{id}
GET       /observations/{id}/taxon_summary
GET       /observations                           :py:func:`~pyinaturalist.v1.observations.get_observations`
POST      /observations
GET       /observations/histogram                 :py:func:`.get_observation_histogram`
GET       /observations/identifiers               :py:func:`.get_observation_identifiers`
GET       /observations/observers                 :py:func:`.get_observation_observers`
GET       /observations/popular_field_values
GET       /observations/species_counts            :py:func:`.get_observation_species_counts`
GET       /observations/taxonomy                  :py:func:`.get_observation_taxonomy`
GET       /observations/updates
PUT       /observations/{id}/viewed_updates
GET       /places/{id}                            :py:func:`.get_places_by_id`
GET       /places/autocomplete                    :py:func:`.get_places_autocomplete`
GET       /places/nearby                          :py:func:`.get_places_nearby`
GET       /posts                                  :py:func:`.get_posts`
DELETE    /project_observations/{id}
PUT       /project_observations/{id}
POST      /project_observations
GET       /projects                               :py:func:`.get_projects`
GET       /projects/{id}                          :py:func:`.get_projects_by_id`
GET       /projects/{id}/members
GET       /projects/{id}/subscriptions
POST      /projects/{id}/add
DELETE    /projects/{id}/remove
GET       /projects/autocomplete
GET       /search                                 :py:func:`.search`
GET       /taxa/{id}                              :py:func:`.get_taxa_by_id`
GET       /taxa                                   :py:func:`.get_taxa`
GET       /taxa/autocomplete                      :py:func:`.get_taxa_autocomplete`
GET       /users/{id}                             :py:func:`.get_user_by_id`
GET       /users/{id}/projects
GET       /users/autocomplete                     :py:func:`.get_users_autocomplete`
GET       /users/me
POST      /photos
========= ======================================= ====================

v0 API
~~~~~~
For all available endpoints, see: https://www.inaturalist.org/pages/api+reference

========= =================================== ====================
Method    Endpoint                            Function
========= =================================== ====================
GET       /observations                       :py:func:`~pyinaturalist.v0.observations.get_observations`
POST      /observations                       :py:func:`.create_observation`
PUT       /observations/{id}                  :py:func:`.update_observation`
DELETE    /observations/{id}                  :py:func:`.delete_observation`
GET       /observation_fields                 :py:func:`.get_observation_fields`
POST      /observation_field_values
PUT       /observation_field_values/{id}      :py:func:`.put_observation_field_values`
DELETE    /observation_field_values/{id}
POST      /observation_photos                 :py:func:`.upload_photos`
POST      /observation_sounds                 :py:func:`.upload_sounds`
========= =================================== ====================
