#!/usr/bin/env python3
"""Example to convert observation locations to TSP format.

This file can then be used to compute the shortest path that hits all locations as a
Traveling Salesperson problem. This only exports a TSP file, which is compatible with many TSP
implementations; it does not solve it.

Extra dependencies:
    `pip install geopy networkx tsplib95`
Example python TSP implementations:
    `pip install acopy`
    `pip install https://github.com/DiegoVicen/som-tsp`
"""
from geopy.distance import distance
from networkx import Graph
from tsplib95.models import StandardProblem

from pyinaturalist.constants import JsonResponse, List


def get_observation_distance(obs1, obs2):
    """Get the distance between the locations of two observations (in meters)"""
    long1, lat1 = obs1["geojson"]["coordinates"]
    long2, lat2 = obs2["geojson"]["coordinates"]
    return distance((lat1, long1), (lat2, long2)).meters


def observations_to_tsp(
    observations: List[JsonResponse], output_file: str = "observations.tsp"
) -> Graph:
    """Convert a list of observations to TSP (traveling salesperson problem) format"""
    problem = StandardProblem()
    problem.comment = f"{len(observations)} iNaturalist observations"
    problem.dimension = len(observations)
    problem.edge_weight_format = "GEO"
    problem.name = "project_observations"
    problem.type = "TSP"

    for i, obs in enumerate(observations):
        long, lat = obs["geojson"]["coordinates"]
        problem.node_coords[i + 1] = [lat, long]

    with open(output_file, "w") as f:
        f.write(problem.render())

    return problem.get_graph()
