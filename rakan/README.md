# Project Rakan

A simple Python API for some redistricting code.

## Compiling

Run `python setup.py build_ext --inplace`.

## Building a State

Using `seed` tool download and create a `networkx` representation of a state.
Pass the file path of the `.nx` file it generates to Rakan command line tool:
`python ./rakan file_path/`

Note the `networkx` file must contain the following properties:

- meta properties:
    - Include _all_ census precincts, including bodies of water and non-precincts.
    - Nodes are referenced by integer (starting from 0)
- node properties:
    - `pop` (integer value) the population of the node.
    - `dis` (integer value) the district number this node is part of (indexed from 0). Use `-1` if no district assigned.
    - `name` (string value) human friendly name of this node.
    - `vertexes` (list of pairs of floats) A list of the coordinates that describe the geogrpahic shape of this node
    <!-- - `edge` (boolean value) true if this node sits on the edge of a map -->
    - (more to come as the project matures)
- graph properties:
    - `fips` (integer value) the FIPS code of the state represented (e.g. 53)
    - `code` (2 digit string) the 2 digit code of the state (e.g. WA)
    - `state` (string) the full state name (e.g. Washington)
    - `districts` (integer) the number of districts in this graph. Use `-1` if no districts assigned.

## Using Parallel processing and Queues for walking

A simple C++ structure has been implemented, where the structure contains basic information on the precinct.