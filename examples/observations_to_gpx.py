#!/usr/bin/env python3
"""
An example of converting observation locations + metadata into GPX format.

Extra dependencies:
    ``pip install gpxpy``
"""
from logging import getLogger

from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint, GPXTrackSegment, GPXWaypoint

from pyinaturalist import Observation, iNatClient
from pyinaturalist.constants import JsonResponse, List

logger = getLogger(__name__)


def observations_to_gpx(
    observations: List[Observation], output_file: str = "observations.gpx", track: bool = True
):
    """Convert a list of observations to a set of GPX waypoints or a GPX track

    Args:
        observations: List of Observation objects
        output_file: File path to write to
        track: Create an ordered GXP track; otherwise, create unordered GPX waypoints
    """
    gpx = GPX()
    logger.info(f"Converting {len(observations)} to GPX points")
    points = [observation_to_gpx_point(obs, track=track) for obs in observations]
    # Filter out any None points (observations without location)
    points = [point for point in points if point is not None]

    if track:
        gpx_track = GPXTrack()
        gpx.tracks.append(gpx_track)
        gpx_segment = GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        gpx_segment.points = points
    else:
        gpx.waypoints = points

    # Save to file
    logger.info(f"Writing GPX data to {output_file}")
    with open(output_file, "w") as f:
        f.write(gpx.to_xml())


def observation_to_gpx_point(observation: Observation, track: bool = True):
    """Convert a single observation to a GPX point

    Args:
        observation: Observation object
        track: Indicates that this point is part of an ordered GXP track;
            otherwise, assume it is an unordered waypoint

    """
    logger.debug(f'Processing observation {observation.id}')
    # Get coordinates from observation location
    if not observation.location:
        logger.warning(f'Observation {observation.id} has no location, skipping')
        return None

    lat, long = observation.location

    # Get medium-sized photo URL, if available; otherwise just use observation URL
    if observation.photos:
        link = observation.photos[0].medium_url or observation.photos[0].url
    else:
        link = observation.uri

    point_cls = GPXTrackPoint if track else GPXWaypoint
    point = point_cls(
        latitude=lat,
        longitude=long,
        time=observation.observed_on,
        comment=str(observation),
    )
    point.description = observation.description
    point.link = link
    point.link_text = f'Observation {observation.id}'
    return point


if __name__ == "__main__":
    # Create a client for API requests
    client = iNatClient()

    # Get search results
    search_params = {
        "project_id": 36883,  # ID of the 'Sugarloaf Ridge State Park' project
        "created_d1": "2020-01-01",  # Get observations from January 2020...
        "created_d2": "2020-09-30",  # ...through September 2020 (adjust these dates as needed)
        "geo": True,  # Only get observations with geospatial coordinates
        "geoprivacy": "open",  # Only get observations with public coordinates (not obscured/private)
    }
    results = client.observations.search(**search_params).all()

    # Convert and write to GPX file
    observations_to_gpx(results)
    # observations_to_tsp(results)
