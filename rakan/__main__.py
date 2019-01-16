from base import BaseRakanWithServer, BaseRakan
from progress.bar import IncrementalBar

import random
import networkx

class Rakan(BaseRakanWithServer):
    """
    An example step
    Argument can be passed in.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def step(self, max_value=1, *more_positional_stuff, **wow_we_got_key_words_up_here):
        # Rakan is able to propose a random move in O(k)
        precinct, district = self.propose_random_move()
        # Completely random
        if random.randint(0, max_value) == 1:
            self.move_precinct(precinct, district)
        
        self.iterations += 1
        print("Moving", precinct, "to district #", district)

    """
    An example walk.
    Perhaps there is specific behavior for the 10 steps
    and specific behavior for the last 10.

    Arguments are completely arbritary and can be rewritten by the user.
    """
    def walk(self, *more_positional_stuff, **wow_we_got_key_words_up_here):
        # for instance:
        for i in range(10):
            self.step(max_value=1)
        
        for i in range(10):
            self.step(max_value=2)

def build_rakan(nx_path):
    """
    Example code to build a Rakan instance
    """
    graph = networkx.read_gpickle(nx_path)
    print("Properties:", graph.graph)
    r = Rakan(len(graph.nodes), graph.graph['districts'])
    
    bar = IncrementalBar("Building Rakan (Step 1: Nodes)", max=len(graph.nodes))
    
    # load up nodes with their respective populations
    for node in sorted(graph.nodes):
        r.add_precinct(graph.nodes[node]['dis'], graph.nodes[node]['pop'])
        if isinstance(r, BaseRakanWithServer):
            r.add_vertexes(node, graph.nodes[node]['vertexes'])
        bar.next()
    
    bar.finish()

    bar = IncrementalBar("Building Rakan (Step 2: Edges)", max=len(graph.edges))

    for (node1, node2) in graph.edges:
        
        r.set_neighbors(node1, node2)
        bar.next()

    bar.finish()

    return r

if __name__ == "__main__":
    rakan = build_rakan("rakan/iowa.dnx")
    # import pdb; pdb.set_trace()
    rakan.walk()