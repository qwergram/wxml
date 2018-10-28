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
import random
from collections import Iterable
import glob

try:
    import requests
    import fiona
    import geopandas
    import networkx
    import shapely
    import plotly
    import plotly.plotly as plt
    import plotly.graph_objs as go
    import plotly.io as pio
    from progress.bar import IncrementalBar
    from progress.spinner import Spinner
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
    with io.open("buildmap/valid_states.json") as handle:
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

    REQUIRES LARGE AMOUNTS OF RAM. Washington state @ block level typically requires 5-6GB of RAM.
    """
    overlappings = 0
    potential_candidates = 0
    failures = 0
    invalids = 0
    bar = IncrementalBar("[!] Creating Edges...", max=len(graph.nodes.data()))
    for gid, geo_data in graph.nodes.data():
        bar.next()
        for gid2, geo_data2 in graph.nodes.data():
            # An absolutely disgusting way to skip nodes we've already looked at.
            # data() doesn't support indexing.
            
            if int(gid2) <= int(gid): continue
            
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

                # If a polygon self-intersects, fix it with buffer(0)
                # this essentially splits the polygon in two.                
                if not polyA.is_valid:
                    polyA = polyA.buffer(0)
                    invalids += 1
                
                if not polyB.is_valid:
                    polyB = polyB.buffer(0)
                    invalids += 1

                try:
                    overlaps = bool(polyA.touches(polyB))
                    overlaps = overlaps or bool(polyA.intersects(polyB))
                except shapely.errors.TopologicalError:
                    # Assume it just doesn't border.
                    overlaps = False
                
                if overlaps:
                    overlappings += 1
                    graph.add_edge(gid, gid2)

            potential_candidates += potential_candidate
            failures += not potential_candidate

    bar.finish()

    log("Found {} potential candidates ({:.2f}% of total)".format(potential_candidates, potential_candidates * 100 / (failures + potential_candidates)))
    log("Found {} overlappings ({:.2f}% of potential candidates)".format(overlappings, overlappings * 100 / potential_candidates))
    log("Found {} invalid polygons ({:.2f}% of total)".format(invalids, invalids * 100 / (failures + potential_candidates)))

    return graph

def load_into_graph(shape):
    """
    Take in a fiona shape file and convert it to a graph.
    O(number of polygons * number of vertexes in polygons)
    """
    # The graph
    graph = networkx.Graph()

    bar = IncrementalBar("[!] Loading polygons as nodes...", max=len(shape))
    # Populate a graph with the usual data
    for i, polygon in enumerate(shape):
        # GeoJSON standard formatting
        fid= polygon['id']
        properties = polygon['properties']
        coordinates = polygon['geometry']['coordinates']
        poly_type = polygon['geometry']['type']

        # Nice to have messages
        bar.next()

        # Sometimes coordinates are nested inside another list.
        # Use generators to avoid killing the computer.

        def flatten_coordinates(iterable):
            for item in iterable:
                if isinstance(item, Iterable) and (len(item) != 2 or not isinstance(item[0], (float, int))):
                    yield from flatten_coordinates(item)
                    # To mark the end of a polygon
                    yield [None, None]
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
        for vertex in coordinates:
            if len(vertex) != 2:
                print(vertex)
            (longitude, lattitude) = vertex
            if longitude == None or lattitude == None: continue
            
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
    
    bar.finish()

    return graph

def draw_graph(graph, name, image=False):
    log("Building Node Trace")
    
    node_trace = go.Scattergeo(
        lat=[graph.nodes.get(node)['avg_lat'] for node in graph.nodes],
        lon=[graph.nodes.get(node)['avg_lon'] for node in graph.nodes],
        mode="markers",
        name="pieces",
        marker={
            "size": 10,
            "line": {"width": 0.9},
            "color": "#bada55"
        },
        hoverinfo="text",
    )
    
    log("Building Edge Trace")

    edge_trace = go.Scattergeo(
        locationmode = 'USA-states',
        lat=[],
        lon=[],
        name="Border",
        mode="lines",
        line={
            "width": 2,
            "color": "#888"
        },
        hoverinfo='none',
    )
    
    bar = IncrementalBar('[!] Building Edges...', max=len(graph.edges))

    for i, (polyA, polyB) in enumerate(graph.edges):
        bar.next()

        if i > 2000: break

        polyA = graph.nodes.get(polyA)
        polyB = graph.nodes.get(polyB)
        ax, ay = polyA['avg_lat'], polyA['avg_lon']
        bx, by = polyB['avg_lat'], polyB['avg_lon']
        edge_trace['lat'] += (ax, bx, None)
        edge_trace['lon'] += (ay, by, None)
    
    bar.finish()

    figure = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            hovermode="closest",
            xaxis={"showgrid": False, "zeroline": False},
            yaxis={"showgrid": False, "zeroline": False},
            geo={
                "scope": 'usa',
                "showland": True,
                "landcolor": "rgb(250, 250, 250)",
                "subunitcolor": "rgb(217, 217, 217)",
                "countrycolor": "rgb(217, 217, 217)",
                "countrywidth": 0.5,
                "subunitwidth": 0.5
            }
        )
    )
    
    if image:
        log("Create image with name {}".format(name))
        return pio.write_image(figure, '{}.png'.format(name))

    log("Create plotly plot with name {}".format(name))
    return plt.plot(figure, filename=name)


def drop_nodes(graph, pieces):
    """
    Select random points in the graph and have it "consume" other points in the graph.
    """
    
    if pieces < len(graph) and pieces > 0:
        drop_count = len(graph) - pieces
        log("Dropping {} nodes to fulfill pieces requirement".format(drop_count))
        
        # Populate a "bag" of nodes
        # In a list for the sake of indexes
        choices = [str(_) for _ in range(len(graph))]
        random.shuffle(choices)

        bar = IncrementalBar('[!] Dropping Nodes...', max=drop_count)

        for i in range(drop_count):
            if i % 100 == 0:
                log("Dropping node #{}".format(i))
            
            # get a random node to drop
            drop = choices.pop()
            
            # get a list of it's neighbors and select one
            old_edges = graph.edges(drop)
            
            if len(old_edges) == 0:
                import pdb; pdb.set_trace()
                continue
            elif len(old_edges) == 1:
                random_index = 0
            else:
                random_index = random.randint(0, len(old_edges) - 1)
            
            for i, edge in enumerate(old_edges):
                # Again, generators don't have indexes
                if i < random_index: continue

                consuming_node = edge[1]
                # Have consuming node inherit all old edges
                for _, other_node in old_edges:
                    graph.add_edge(consuming_node, other_node)
                break
            
            graph.remove_node(drop)

            bar.next()

        bar.finish()
        
    return graph

def cache_network(graph):
    networkx.write_gpickle(graph, "graph_cache.networkx")

def main(args):
    """
    Run script with -h flag for documentation on main.
    """
    # First, validate the map
    if not is_valid_state(args.state):
        raise ValueError("Unknown State: {}".format(args.state))

    if os.path.isfile("graph_cache.networkx"):
        log("Detected cached graph")
        graph = networkx.read_gpickle("graph_cache.networkx")

    else:
        log("Building Graph for {}".format(args.state))
        seed_map = None
        
        if args.granularity == "block":
            seed_map = seed_blocks(args.state)
        elif args.granularity == "county":
            seed_map = seed_counties(args.state)
        # elif args.granularity == "precinct":
        #     log("Seeding Precincts...")
        elif args.granularity == "file":
            target = glob.glob('file_input/*.shp')[0]
            log("Seeding from {}".format(target))
            seed_map = fiona.open(target)

        # Generate a map given seed
        graph = drop_nodes(connect_nodes(load_into_graph(seed_map)), args.pieces)
        
        # Cache network
        cache_network(graph)

    # Output the graph
    if args.output == "plotly" or args.output == "all":
        # Plotly graph
        draw_graph(graph, args.state)
    if args.output == "weifan" or args.output == "all":
        # weifan's adjacency graph format
        pass
    if args.output == "geoJson" or args.output == "all":
        # geoJson output
        pass
    if args.output == "image" or args.output == "all":
        # image output
        draw_graph(graph, args.state, True)

if __name__ == "__main__":
    log("Initial Graph Builder Script")
    
    parser = argparse.ArgumentParser(description="""
    A tool that takes in a state and splits it up into n pieces. Piece granularity is defined by the user.
    VERSION: {}
    """.format(__VERSION__))

    # Random Generation Parameters
    parser.add_argument("state", type=str, help="A state code (such as 53_WASHINGTON).")
    parser.add_argument("granularity", default="precinct", choices=["block", "county", "precinct", "file"], type=str, help="How large the initial chunks should be. If file, checks directory file_input/")
    parser.add_argument("output", type=str, choices=["all", "weifan", "geoJson", "image", "plotly"], help="Format of output.")
    parser.add_argument("-pieces", type=int, default=0, help="Number of pieces to split the state into. Pass nothing to maintain pieces defined by state set. Passing in a value less than the seed data will result in a noop.")
    # parser.add_argument("-offload", type=bool, default=True, help="Execute script on remote server (Will be roughly 30% - 50% faster than any laptop, but I get to keep your data :).")
    parser.add_argument("-v", type=bool, default=False, help="Execute with output")

    # Check inputs are valid
    args = parser.parse_args()

    # Set LOGGER verbosity
    VERBOSE = args.v

    # Run
    main(args)
