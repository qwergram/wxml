"""
A simple tool for building random precinct maps.

- Read US Census data/Generate random data
- Build precinct node map
- Divide it into n districts quickly

Norton Pengra - nortonjp@uw.edu - github.com/pengra
"""

__VERSION__ = 0.01
TYPE_CHECK = True

import sys
import argparse
import json
import io
import os
from collections import Iterable

try:
    import requests
    import fiona
    import geopandas
    import networkx
    import shapely
except ImportError:
    raise ImportError("Requires 3rd party library, did you do `pip install -r requirements.txt`?")

from util import *

# APIs for geography data.
US_CENSUS_API = "https://www2.census.gov/geo/tiger/TIGER2009/"
# CACHE_API = "https://data.pengra.io/state_gis/"

# For LOGGER
VERBOSE = False

def log(*args, **kwargs):
    if VERBOSE:
        print('[!]', *args, **kwargs)

def is_valid_state(state):
    """
    Check if the passed in state exists in the valid_states.json file.
    """
    log("Validating State...")
    with io.open("initial_builder/valid_states.json") as handle:
        valid_states = json.loads(handle.read())
    return state in valid_states


def seed_census_api(state, granularity):
    """
    Build an initial node graph from US Census site.
    """
    log("Downloading state {} data".format(granularity))

    # Get state_id/state and use it to define file/directory names
    state_id, state_name = state.split('_', 1)
    filename = "tl_2009_{}_{}".format(state_id, granularity)
    dirname = "{}/".format(state_id)

    if not os.path.isdir(dirname):
        if not os.path.isfile(filename):
            download_file(US_CENSUS_API + state + "/" + filename + ".zip")
        unzip(filename + ".zip", dirname)
    
    log("Loading state {} data into memory".format(granularity))
    
    shape = fiona.open(dirname + filename + ".shp")
    return shape


def seed_pengra_api(state, granularity):
    """
    Build an initial node graph using personal API.
    """
    raise NotImplementedError("Server still being worked on.")


def seed_blocks(state):
    """
    Build an initial node graph from blocks.
    Data comes from US Census.
    """
    return seed_census_api(state, "tabblock")


def seed_counties(state):
    """
    Build an initial node graph from counties.
    Data comes from US Census.
    """
    return seed_census_api(state, "county")


def min_max_collision_check(polygonACoordinates, polygonBCoordinates):
    """
    Check if the polygons overlap each other 
    when projected to the x axis and y axis.
    """

def connect_nodes(graph):
    """
    Create an adjacency matrix given a set of vertexes.
    First, check if the polygons overlap when projected to the x and y axis.
    In Washington, this check eliminates 50%-96% of all paired polygons depending on granularity.
    Typically, the smaller the granularity, the higher the elimnation rates.
    
    If their projections overlap, start to do the expensive C++ implemented Weiler-Atherton checks.

    ## Notes:
    GIS Alternative (not automatic): http://desktop.arcgis.com/en/arcmap/latest/tools/analysis-toolbox/how-polygonneighbors-analysis-works.htm
    
    ## References:
    The fantastic Algorithm: https://en.wikipedia.org/wiki/Weiler–Atherton_clipping_algorithm

    ## Performance Notes:
    Worst case (everything is connected to everything): o(n^4)
    Best case (no adjacencies): o(n^2) 
    
    Server will execute this code in roughly 40-50% faster than laptop.

    REQUIRES LARGE AMOUNTS OF RAM. Washington state @ block level typically requires 3-4GB of RAM.
    """
    overlappings = 0
    potential_candidates = 0
    failures = 0
    for gid, geo_data in graph.nodes.data():
        
        if int(gid) % 100 == 0:
            log("Connecting Node #{} to others".format(gid))
        
        for gid2, geo_data2 in graph.nodes.data():
            # An absolutely disgusting way to skip nodes we've already looked at.
            # data() doesn't support indexing.
            if int(gid2) < int(gid): continue
            
            # check if they overlap when projected to 1d
            potential_candidate = (
                (geo_data['min_lon'] <= geo_data2['max_lon'] and 
                geo_data2['min_lon'] <= geo_data['max_lon']) or
                (geo_data['min_lat'] <= geo_data2['max_lat'] and 
                geo_data2['min_lat'] <= geo_data['max_lat'])
            )

            if potential_candidate:
                # Expensive.
                
                polyA = shapely.geometry.Polygon(geo_data['vertexes'])
                polyB = shapely.geometry.Polygon(geo_data2['vertexes'])
                try:
                    overlaps = polyA.touches(polyB)
                except shapely.errors.TopologicalError:
                    # Assume it just doesn't border.
                    overlaps = False
                
                if overlaps:
                    graph.add_edge(gid, gid2)

            potential_candidates += potential_candidate
            failures += not potential_candidate

    log("Found {} potential candidates ({:.2f}% of total)".format(potential_candidates, potential_candidates * 100 / (failures + potential_candidates)))
    log("Found {} overlappings ({:.2f}% of potential candidates)".format(overlappings, overlappings * 100 / potential_candidates))

    return graph


def load_into_graph(shape):
    """
    Take in a fiona shape file and convert it to a graph.
    O(number of polygons * number of vertexes in polygons)
    """
    # The graph
    graph = networkx.Graph()

    # Populate a graph with the usual data
    for i, polygon in enumerate(shape):
        # GeoJSON standard formatting
        fid= polygon['id']
        properties = polygon['properties']
        coordinates = polygon['geometry']['coordinates']

        # Nice to have messages
        if i % 100 == 0:
            log("Loading Polygon #{}".format(i))

        # Sometimes coordinates are nested inside another list.
        # Use generators to avoid killing the computer.
        def flatten_coordinates(iterable):
            for item in iterable:
                if isinstance(item, Iterable) and len(item) != 2:
                    yield from flatten_coordinates(item)
                else:
                    yield item
        
        coordinates = flatten_coordinates(coordinates)
        
        # Set mins/maxes to first item in dataset
        # These values are safe because world coordinates
        # are between -180 and 180.
        minimum_long = 999
        maximum_long = -999
        minimum_lat = 999
        maximum_lat = -999
        
        # For calculating averages
        sum_long = 0
        sum_lat = 0
        total = 0

        # make a copy of coordinates
        vertexes = []
        
        # Find min/max
        for (longitude, lattitude) in coordinates:
            total += 1
            sum_long += longitude
            sum_lat += lattitude

            # Store as vertex
            vertexes.append((longitude, lattitude))

            # Pythonic way of finding mins/maxes
            minimum_lat = min([minimum_lat, lattitude])
            minimum_long = min([minimum_long, longitude])
            maximum_lat = max([lattitude, maximum_lat])
            maximum_long = max([longitude, maximum_long])

        graph.add_node(
            fid,  # GIS decided indexes.
            vertexes=vertexes,
            # For quickly determining if a x/y axis projected polygons overlap
            min_lon=minimum_long,
            max_lon=minimum_long,
            min_lat=minimum_lat,
            max_lat=maximum_lat,
            # For determining which polygon is more north/west/east/south
            avg_lon=sum_long / total, 
            avg_lat=sum_lat / total,
            **properties
        )

    return graph


def main(args):
    """
    Run script with -h flag for documentation on main.
    """
    # First, validate the map
    if not is_valid_state(args.state):
        raise ValueError("Unknown State: {}".format(args.state))

    log("Building Graph for {}".format(args.state))
    seed_map = None
    
    if args.granularity == "block":
        seed_map = seed_blocks(args.state)
    elif args.granularity == "county":
        log("Seeding Counties...")
        seed_map = seed_counties(args.state)
    # elif args.granularity == "precinct":
    #     log("Seeding Precincts...")

    graph = connect_nodes(load_into_graph(seed_map))
    

if __name__ == "__main__":
    log("Initial Builder Script by Norton Pengra")
    
    parser = argparse.ArgumentParser(description="""
    A tool that takes in a state and splits it up into n pieces. Piece granularity is defined by the user.
    VERSION: {}
    """.format(__VERSION__))

    # Random Generation Parameters
    parser.add_argument("state", type=str, help="A state code (such as 53_WASHINGTON).")
    parser.add_argument("granularity", default="precinct", choices=["block", "county", "precinct"], type=str, help="How large the initial chunks should be.")
    parser.add_argument("output", type=str, help="Name of file to output.")
    parser.add_argument("-pieces", type=int, help="Number of pieces to split the state into. Pass nothing to maintain pieces defined by state set.")
    # parser.add_argument("-offload", type=bool, default=True, help="Execute script on remote server (Will be faster than any laptop).")
    parser.add_argument("-visualize", type=bool, default=False, help="Execute script and output a quick image of produced map.")
    parser.add_argument("-v", type=bool, default=False, help="Execute with output")

    # Check inputs are valid
    args = parser.parse_args()

    # Set LOGGER verbosity
    VERBOSE = args.v

    # Run
    main(args)
