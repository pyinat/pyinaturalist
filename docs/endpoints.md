(endpoints)=
# {fa}`table` Endpoint Summary

Below is a list of iNaturalist API endpoints that have either been added or may be added in the
future, along with their corresponding functions in pyinaturalist.

## v1 API
For all available endpoints, see: <http://api.inaturalist.org/v1/docs/>

| Method | Endpoint                           | Function
| ------ | --------                           | --------
| POST   | /annotations                       |
| DELETE | /annotations/{id}                  |
| POST   | /comments                          |
| DELETE | /comments/{id}                     |
| PUT    | /comments/{id}                     |
| GET    | /controlled_terms                  | {py:func}`.get_controlled_terms`
| GET    | /controlled_terms/for_taxon        | {py:func}`.get_controlled_terms`
| GET    | /identifications                   | {py:func}`.get_identifications`
| GET    | /identifications/{id}              | {py:func}`.get_identifications_by_id`
| GET    | /identifications/species_counts    |
| GET    | /identifications/identifiers       |
| GET    | /identifications/observers         |
| GET    | /identifications/similar_species   |
| GET    | /messages                          | {py:func}`.get_messages`
| GET    | /messages/{id}                     | {py:func}`.get_message_by_id`
| GET    | /messages/unread                   | {py:func}`.get_unread_meassage_count`
| DELETE | /observation_field_values/{id}     | {py:func}`.delete_observation_field`
| PUT    | /observation_field_values/{id}     | {py:func}`.set_observation_field`
| POST   | /observation_field_values          | {py:func}`.set_observation_field`
| POST   | /observation_photos                | {py:func}`.upload`
| POST   | /observation_sounds                | {py:func}`.upload`
| DELETE | /observations/{id}                 | {py:func}`~pyinaturalist.v1.observations.delete_observation`
| GET    | /observations/{id}                 | {py:func}`.get_observations_by_id`
| PUT    | /observations/{id}                 | {py:func}`~pyinaturalist.v1.observations.update_observation`
| GET    | /observations/{id}/taxon_summary   | {py:func}`.get_observation_taxon_summary`
| GET    | /observations                      | {py:func}`~pyinaturalist.v1.observations.get_observations`
| POST   | /observations                      | {py:func}`~pyinaturalist.v1.observations.create_observation`
| GET    | /observations/histogram            | {py:func}`.get_observation_histogram`
| GET    | /observations/identifiers          | {py:func}`.get_observation_identifiers`
| GET    | /observations/observers            | {py:func}`.get_observation_observers`
| GET    | /observations/popular_field_values | {py:func}`.get_observation_popular_field_values`
| GET    | /observations/species_counts       | {py:func}`.get_observation_species_counts`
| GET    | /observations/taxonomy             | {py:func}`.get_observation_taxonomy`
| GET    | /places/{id}                       | {py:func}`.get_places_by_id`
| GET    | /places/autocomplete               | {py:func}`.get_places_autocomplete`
| GET    | /places/nearby                     | {py:func}`.get_places_nearby`
| GET    | /posts                             | {py:func}`.get_posts`
| GET    | /projects                          | {py:func}`.get_projects`
| GET    | /projects/{id}                     | {py:func}`.get_projects_by_id`
| PUT    | /projects/{id}                     | {py:func}`.update_project`
| GET    | /projects/{id}/members             |
| GET    | /projects/{id}/subscriptions       |
| POST   | /projects/{id}/add                 | {py:func}`.add_project_observation`
| DELETE | /projects/{id}/remove              | {py:func}`.delete_project_observation`
| GET    | /projects/autocomplete             |
| GET    | /search                            | {py:func}`.search`
| GET    | /taxa                              | {py:func}`.get_taxa`
| GET    | /taxa/{id}                         | {py:func}`.get_taxa_by_id`
| GET    | /taxa/{id}/map_layers              | {py:func}`.get_taxa_map_layers`
| GET    | /taxa/autocomplete                 | {py:func}`.get_taxa_autocomplete`
| GET    | /users/{id}                        | {py:func}`.get_user_by_id`
| GET    | /users/{id}/projects               |
| GET    | /users/autocomplete                | {py:func}`.get_users_autocomplete`
| GET    | /users/me                          |

## v0 API
For all available endpoints, see: <https://www.inaturalist.org/pages/api+reference>

| Method | Endpoint                        | Function
| ------ | --------                        | --------
| GET    | /observations                   | {py:func}`~pyinaturalist.v0.observations.get_observations`
| POST   | /observations                   | {py:func}`~pyinaturalist.v0.observations.create_observation`
| PUT    | /observations/{id}              | {py:func}`~pyinaturalist.v0.observations.update_observation`
| DELETE | /observations/{id}              | {py:func}`~pyinaturalist.v0.observations.delete_observation`
| GET    | /observation_fields             | {py:func}`.get_observation_fields`
| PUT    | /observation_field_values/{id}  | {py:func}`.put_observation_field_values`
| POST   | /observation_photos             | {py:func}`.upload_photos`
| POST   | /observation_sounds             | {py:func}`.upload_sounds`
