## Implemented Endpoints
Below is a complete list of iNaturalist API endpoints, and the subset of them that have been
implemented in pyinaturalist.

### Node-based API
For full documentation, see: http://api.inaturalist.org/v1/docs/

Method            | Endpoint                                    | Implemented
------            | ------                                      | ------
POST              | /annotations                                |
DELETE            | /annotations/{id}                           |
POST              | /votes/vote/annotation/{id}                 |
DELETE            | /votes/unvote/annotation/{id}               |
POST              | /comments                                   |
DELETE            | /comments/{id}                              |
PUT               | /comments/{id}                              |
GET               | /controlled_terms                           |
GET               | /controlled_terms/for_taxon                 |
POST              | /flags                                      |
DELETE            | /flags/{id}                                 |
PUT               | /flags/{id}                                 |
DELETE            | /identifications/{id}                       |
GET               | /identifications/{id}                       |
PUT               | /identifications/{id}                       |
GET               | /identifications                            |
POST              | /identifications                            |
GET               | /identifications/categories                 |
GET               | /identifications/species_counts             |
GET               | /identifications/identifiers                |
GET               | /identifications/observers                  |
GET               | /identifications/recent_taxa                |
GET               | /identifications/similar_species            |
GET               | /messages                                   |
POST              | /messages                                   |
DELETE            | /messages/{id}                              |
GET               | /messages/{id}                              |
GET               | /messages/unread                            |
DELETE            | /observation_field_values/{id}              |
PUT               | /observation_field_values/{id}              |
POST              | /observation_field_values                   |
DELETE            | /observation_photos/{id}                    |
PUT               | /observation_photos/{id}                    |
POST              | /observation_photos                         |
DELETE            | /observations/{id}                          |
GET               | /observations/{id}                          | yes
PUT               | /observations/{id}                          |
POST              | /observations/{id}/fave                     |
DELETE            | /observations/{id}/unfave                   |
POST              | /observations/{id}/review                   |
POST              | /observations/{id}/unreview                 |
GET               | /observations/{id}/subscriptions            |
DELETE            | /observations/{id}/quality/{metric}         |
POST              | /observations/{id}/quality/{metric}         |
GET               | /observations/{id}/taxon_summary            |
POST              | /subscriptions/observation/{id}/subscribe   |
POST              | /votes/vote/observation/{id}                |
DELETE            | /votes/unvote/observation/{id}              |
GET               | /observations                               |
POST              | /observations                               |
GET               | /observations/deleted                       |
GET               | /observations/histogram                     |
GET               | /observations/identifiers                   |
GET               | /observations/observers                     |
GET               | /observations/popular_field_values          |
GET               | /observations/species_counts                | yes
GET               | /observations/updates                       |
PUT               | /observations/{id}/viewed_updates           |
GET               | /places/{id}                                | yes
GET               | /places/autocomplete                        | yes
GET               | /places/nearby                              | yes
GET               | /posts                                      |
POST              | /posts                                      |
DELETE            | /posts/{id}                                 |
PUT               | /posts/{id}                                 |
GET               | /posts/for_user                             |
DELETE            | /project_observations/{id}                  |
PUT               | /project_observations/{id}                  |
POST              | /project_observations                       |
GET               | /projects                                   | yes
GET               | /projects/{id}                              | yes
POST              | /projects/{id}/join                         |
DELETE            | /projects/{id}/leave                        |
GET               | /projects/{id}/members                      |
GET               | /projects/{id}/subscriptions                |
POST              | /projects/{id}/add                          |
DELETE            | /projects/{id}/remove                       |
GET               | /projects/autocomplete                      |
POST              | /subscriptions/project/{id}/subscribe       |
GET               | /search                                     |
GET               | /taxa/{id}                                  | yes
GET               | /taxa                                       | yes
GET               | /taxa/autocomplete                          | yes
GET               | /users/{id}                                 |
PUT               | /users/{id}                                 |
GET               | /users/{id}/projects                        |
GET               | /users/autocomplete                         |
GET               | /users/me                                   |
DELETE            | /users/{id}/mute                            |
POST              | /users/{id}/mute                            |
PUT               | /users/update_session                       |
GET               | /colored_heatmap/{zoom}/{x}/{y}.png         |
GET               | /grid/{zoom}/{x}/{y}.png                    |
GET               | /heatmap/{zoom}/{x}/{y}.png                 |
GET               | /points/{zoom}/{x}/{y}.png                  |
GET               | /places/{place_id}/{zoom}/{x}/{y}.png       |
GET               | /taxon_places/{taxon_id}/{zoom}/{x}/{y}.png |
GET               | /taxon_ranges/{taxon_id}/{zoom}/{x}/{y}.png |
GET               | /colored_heatmap/{zoom}/{x}/{y}.grid.json   |
GET               | /grid/{zoom}/{x}/{y}.grid.json              |
GET               | /heatmap/{zoom}/{x}/{y}.grid.json           |
GET               | /points/{zoom}/{x}/{y}.grid.json            |
POST              | /photos                                     |
                  

### Rails-Based API
For full documentation, see: https://www.inaturalist.org/pages/api+reference

Method            | Endpoint                                    | Implemented
------            | ------                                      | ------
POST              | /comments                                   |
PUT               | /comments/{id}                              |
DELETE            | /comments/{id}                              |
POST              | /identifications                            |
PUT               | /identifications/{id}                       |
DELETE            | /identifications/{id}                       |
GET               | /observations                               | yes
POST              | /observations                               | yes
GET               | /observations/{id}                          | yes
PUT               | /observations/{id}                          | yes
DELETE            | /observations/{id}                          | yes
POST              | /observations/{id}/quality/:metric          |
DELETE            | /observations/{id}/quality/:metric          |
PUT               | /observations/{id}/viewed_updates           |
GET               | /observations/:username                     |
GET               | /observations/project/{id}                  |
GET               | /observations/taxon_stats                   |
GET               | /observations/user_stats                    |
GET               | /observation_fields                         | yes
POST              | /observation_field_values                   |
PUT               | /observation_field_values/{id}              | yes
DELETE            | /observation_field_values/{id}              |
POST              | /observation_photos                         | yes
GET               | /places                                     |
GET               | /projects                                   |
GET               | /projects/{id}                              |
GET               | /projects/{id}/contributors.widget          |
GET               | /projects/user/:login                       |
GET               | /projects/{id}/members                      |
POST              | /projects/{id}/join                         |
DELETE            | /projects/{id}/leave                        |
POST              | /project_observations                       |
POST              | /users                                      |
PUT               | /users/{id}                                 |
GET               | /users/edit                                 |
GET               | /users/new_updates                          |
