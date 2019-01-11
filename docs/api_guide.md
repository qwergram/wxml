# API Guide

## API method Complexity

Complexity of each method will be notated as $O(n)$ format. The following symbols are represented as so:

- $p$ - the number of precincts Rakan is tracking
- $d$ - the number of districts Rakan is tracking
- $d_n$ - the number of precincts in district $n$
- $n_p$ - the number of neighbors of precinct $p$
- $e$ - the number of edges between all precincts
- $u$ - the number of unchecked districts.
- $k$ - a constant

## API Public vs Protected vs Private Guide

!!! success "ClassName::method_name(params)"
    A check mark + API details indicates this is a `public` API method, designed for all users to use.

!!! warning "ClassName::_method_name(params)"
    A warning + API details indicates this is a `public` API method, designed for debugging, these methods are designed for all users to use, but face significant slowdowns when called in Python code. They're much faster when called from C++.

!!! danger "ClassName::__method_name(params)"
    A danger + API details indicates this is a `private` API method (but users can still access it).
    This implies this method is unsafe, and should only be modified under certain circumstances.

## Important Implementation Details

!!! note "RIDs"
    Note that `rid` will refer to Rakan's internal ID system. `rid` are guaranteed to be unique, non-negative and continuous.
    An `rid` refers to a precinct or precinct piece if a precinct consists of multiple polygons.

!!! note "District IDs"
    A district in Rakan will always be represented as a unique non-negative integer.

## Base Class

The idea is that users can begin with the following base class:

```py
# rakan/__main__.py
from rakan import PyRakan as BaseRakan
import random

class Rakan(BaseRakan):
    """
    An example step
    Argument can be passed in.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def step(self, max_value=1, *args, **kwargs):
        # Rakan is able to propose a random move in O(d)
        precinct, district = self.propose_random_move()
        # Completely random
        if random.randint(0, max_value) == 1:
            self.move_precinct(precinct, district)

    """
    An example walk.
    Perhaps there is specific behavior for the 10 steps
    and specific behavior for the last 10.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def walk(self, *args, **kwargs):
        # for instance:
        for i in range(10):
            self.step(max_value=1)

        for i in range(10):
            self.step(max_value=2)
```

Users are then able to modify step, and walk to their liking. The users have access to the following methods on `Rakan`.

## Rakan API

!!! success "Rakan::\_\_init\_\_(int size = 10000, int districts = 100)"
    Rakan needs to know the number of precincts (`size` as an integer) and the number districts (`districts` as an integer).
    The default values are listed in the constructor above.

    Time Complexity: $O(k)$

    Memory Complexity: $O(2p + d + e)$

### API for Constructing Rakan

There's no way to remove a precinct/neighbor once added/set at the moment.
It's best to perform operations on a `networkx` graph that may require "undoing" precinct/neighbor additions.
Once satisfied with the graph, then add it all to Rakan without issues.

!!! success "Rakan::add_precinct(int district, int population = 0)"
    Add a precinct (rather node) to Rakan.
    Pass in the district and population of the node being added.
    A district is required, but a population isn't, by default it is 0.
    This method returns the `rid` of the newly added node.

    Note that _all_ nodes in a `.rnx` file presented by Blitz should be added to Rakan via `add_precinct`.
    This means multi-polygon precincts should be split and added as separate precincts.
    Additionally, water bodies and non-precincts (such as national park territory) should be added as well.
    You may ignore this warning if your walk does require that a node to be reachable from every other node.

    Time Complexity: $O(k)$

    Memory Complexity: $O(k)$

!!! success "Rakan::set_neighbors(int rid1, int rid2)"
    Set two `rid`s to be neighbors. 
    Both `rid`s must have had been already added to Rakan via `add_precinct`.

    Time Complexity: $O(k)$

    Memory Complexity: $O(k)$

### API for Writing a Walk

General purpose API implemented in such a way that it runs faster than doing it in Python `dict`s/`list`s.

!!! success "Rakan::districts"
    Return a list of lists of integers.
    The list of integers at the `n`th index represents the RIDs in district `n`.
    For instance, if the following was the return value of `.districts`:

    ```
    [
        [3],
        [0, 1],
        [2]
    ]
    ```

    That would imply:

    - District 0 contains precinct 3
    - District 1 contains precincts 0 and 1
    - District 2 contains precinct 2

    Time Complexity: $O(k)$

!!! warning "Rakan::precincts"
    Return a list of Precinct objects.
    `ids` (not `rids`) of these objects are not permanent.
    May cause comparison issues if `rids` change (which you shouldn't do anyways).
    See the precinct API to see what operations can be done with precincts.

    Calling this is much faster in C++.

    Time Complexity: $O(p)$ (In C++: $O(k)$)

!!! success "Rakan::edges"
    Return a list of tuple pairs.
    The index of the list represents the `rid` of the node in question.
    The first item in the pair is a list of adjacent nodes in different districts.
    The second item in the pair is a list of adjacent nodes in the same district.
    For instance, if the return value is as so:

    ```
    [
        ([1], [2]),
        ([0, 2], []),
        ([1], [0]),
        ([], [])
    ]
    ```

    Then the node with rid `0` is connected to nodes `1` and `2`, where `1` is in a different district and `2` is in the same district.
    Node `1` is connected to districts `0` and `2` but both are in different districts.
    Node `2` is connected to nodes `1` and `2`, where `1` is in a different district and `0` is in the same district.
    Node `3` is not connected to any other nodes (consequently, this graph is technically invalid).

    Time Complexity: $O(k)$

!!! success "Rakan::get_neighbors(int rid)"
    Retrieve a dictionary, where keys are district (integers) and values are lists of rids (list of integers).
    For instance, when querying the neighbors of rid `0` returns

    ```
    {
        1: [2, 3],
        2: [1]
    }
    ```

    This means that node `0` has two neighbors: node `2` and `3` (in district 1) and node `1` (in district 2).

    Time Complexity: $O(n_p)$

!!! success "Rakan::get_diff_district_neighbors(int rid)"
    Same exact API as `get_neighbors` but excludes all neighbors in the same district.
    Saves the user a conditional statement in python when trying to get different district neighbors.

    Time Complexity: $O(n_p)$

!!! success "Rakan::are_connected(int rid1, int rid2, int black_listed_rid = -1)"
    Performs a BFS from both specified `rid`s until the "net" of the BFS from either side touches each other.
    The BFS will only traverse through other nodes that are in the same district as `rid1` and `rid2`.
    The BFS will also not traverse through `black_listed_rid` (by default, black_listed_rid is `-1`, no node has this rid so BFS will take any path it can take).

    This method returns true if it is possible to reach `rid1` from `rid2` through a traversal of nodes in the same district.
    Returns false otherwise.
    Code takes the longest to execute if the two specified `rid`s are not connected.

    Time Complexity: $O(d_n)$

    Memory Complexity: $O(d_n)$

!!! success "Rakan::is_valid()"
    Returns true if Rakan is currently in a valid state. 
    Rakan is in a valid state if the following are all true.

    - Each district has at least 2 nodes.
    - Each node in all districts can be reached from any other node in the same district.

    Rakan will only perform checks on `rid`s listed in `_unchecked_changes`.
    When it reaches a conclusion, `_unchecked_changes` is cleared of all its "valid" items and a cached value is returned upon successive calls of this method so long as Rakan doesn't perform any unchecked moves.

    Time Complexity: $O(\sum_{i\in u}{n_i})$ ($O(k)$ when `_unchecked_changes` is empty)

    Memory Complexity: $O(d_n)$ ($O(0)$ when `_unchecked_changes` is empty)

!!! success "Rakan::propose_random_move()"
    Rakan is able to propose a random move by retrieving two random and neighboring nodes that are in different districts.
    It then selects one of the random nodes and proposes that it take the district of the other node.
    Note that each edge (of two nodes of different districts) in Rakan are _equally_ likely to be selected.

    For instance, if the method returns `(1, 2)`, the method is proposing node with `rid` `1` to become a part of district `2`.

    Note this means the move it proposes could sever a district into two parts.
    It's best to make this move with `move_precinct`, where the method will throw an exception if the move is invalid.

    Time Complexity: $O(d + d_n)$ (where $d_n$ is the district the proposed `rid` is in)

!!! success "Rakan::move_precinct(int rid, int district)"
    Move the following `rid` and change its district to `district`. Performs the following checks before making the move:

    - Checks if Rakan is currently in a valid state
    - Checks if one of the neighbors of `rid` has the district `district`.
    - Checks if the move will split a district into two pieces.

    The complexity of these checks are as follows:

    - $O(\sum_{i\in u}{n_i})$ ($O(k)$ when `_unchecked_changes` is empty)
    - $O(n_p)$ (where $p$ is `rid`)
    - $O(D_pd_pn_p)$ (where $p$ is `rid` and $D_p$ are the number of districts touching `rid`)

    When checks all pass, the operation to make the move is $O(d_p + n_p^2)$.
    Since checks were already performed, this rid is not added to `_unchecked_changes`, but instead added to `_checked_changes`.

    Time Complexity: $O(\sum_{i\in u}{n_i} + n_p + D_pd_pn_p + d_p + n_p^2)$ (where $p$ is `rid` and $D_p$ are the number of districts touching `rid`)

### API for Internal Debugging

!!! danger "Rakan::\_unchecked\_changes"
    Return a list of `rids` that have had operations performed on them, but haven't been confirmed to result in a valid graph.

    Time Complexity: $O(k)$

!!! danger "Rakan::\_checked\_changes"
    Return a list of `rids` that have had operations performed on them _and_ been confirmed to result in a valid graph.

    Time Complexity: $O(k)$


## Precinct API