"""
A simple tool for listing important information about shape files.

- Will generate a report that discloses:
    - Which precincts have no population data
    - Which precincts are in multiple pieces
        - And how to group these multiple pieces

- Write out a new shape file with none of these issues.

Norton Pengra - nortonjp@uw.edu - github.com/pengra
"""

__VERSION__ = 0.01
VERBOSE = False

import argparse
import glob
import os
import io

try:
    import fiona
    from progress.bar import IncrementalBar
except ImportError:
    raise ImportError("Requires 3rd party library, did you do `pip install -r requirements.txt`?")

from util import *


def get_shape_file(dir_location):
    """
    Check if a path contains a shape file.
    """
    if os.path.isdir(dir_location):
        path = glob.glob(os.path.join(dir_location, "*.shp"))
        if len(path) >= 1:
            return fiona.open(path[0])
    return []


def iterate_shape(shape, precinct_flag, population_flag, land_flag, population_threshold, land_threshold, primary_key, show_bar=True):
    """
    Iterate through the polygons declared in a shape file.
    Returns 
    """
    if show_bar:
        bar = IncrementalBar("[!] Reading Shapes... ", max=len(shape))
    flags = 0
    for i, polygon in enumerate(shape):
        # GeoJSON standard formatting
        flag = False

        fid = polygon['id']
        properties = polygon['properties']
        coordinates = polygon['geometry']['coordinates']
        poly_type = polygon['geometry']['type']

        precinct_id = properties.get(precinct_flag)
        wa_geo_id = properties.get(primary_key)

        if properties[population_flag] <= population_threshold:
            flag = True
        
        if poly_type.lower() != "polygon":
            flag = True
        
        if precinct_flag in [None, "NA"]:
            flag = True

        if properties[land_flag] <= land_threshold:
            flag = True

        yield (flag, wa_geo_id, precinct_id, properties[population_flag], poly_type)
        
        if show_bar:
            bar.next()
    
    if show_bar:
        bar.finish()


def output_results(issues):
    print("primary key\tprecinct\tpopulation\tpolygon type")
    for report in issues:
        flag, primary_key, precinct_id, population, poly_type = report
        if flag:
            print("\t".join([str(_) for _ in [primary_key, precinct_id, population, poly_type]]))


def write_results(issues):
    print("Writing Report")
    with io.open("report.tsv", "w") as handle:
        handle.write("primary key, precinct, population, polygon type\n")
        for report in issues:
            flag, primary_key, precinct_id, population, poly_type = report
            if flag:
                handle.write(", ".join(['"' + str(_) + '"' for _ in [primary_key, precinct_id, population, poly_type]]))
                handle.write("\n")

def main(args):
    shape = get_shape_file(args.path)
    issues = iterate_shape(shape, args.precinct_flag, args.population_flag, args.land_flag, args.population_threshold, args.land_threshold, args.primary_key, args.output == "txt")

    if args.output == "stdout":
        output_results(issues)
    elif args.output == "txt":
        write_results(issues)
    

if __name__ == "__main__":
    log("Bad Shapefile Reporter Script")
    
    parser = argparse.ArgumentParser(description="""
    A tool that takes in a shape file (split into precincts) and applies filters described below.
    VERSION: {}
    """.format(__VERSION__))

    # Random Generation Parameters
    parser.add_argument("path", type=str, help="A relative or absolute filepath to shapefile directory.")
    parser.add_argument("primary_key", default="WA_GEO_ID", type=str, help="Which field is the primary key. For instance, \"WA_GEO_ID\"")
    parser.add_argument("precinct_flag", default="", type=str, help="Which field the precinct ID is declared in.")
    parser.add_argument("population_flag", default="", type=str, help="What attribute represents population in shape file.")
    parser.add_argument("land_flag", default="", type=str, help="What attribute represents land mass in shape file.")
    parser.add_argument("output", type=str, default="stdout", choices=["stdout", "txt"], help="Format of output.")
    parser.add_argument("-population-threshold", default=0, type=int, help="Precinct must have at least this many people to be considered valid. Default is 0.")
    parser.add_argument("-land-threshold", default=0, type=int, help="Precinct must have at least this much land to be considered valid. Default is 0.")
    parser.add_argument("-v", type=bool, default=False, help="Execute with debugging output")

    # Check inputs are valid
    args = parser.parse_args()

    # Set LOGGER verbosity
    VERBOSE = args.v

    # Run
    main(args)