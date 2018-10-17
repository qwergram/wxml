class BaseGraph(Confg):

    class _Meta:
        abstract = True

    def __init__(self, title):
        """Create an empty Precinct Map.
        This class should be used as an abstract class.
        """
        assert isinstance(title, str), "Title must be a string"
        
        # Track what has been run and what hasn't
        self._runtime_state = {
            EDGE_TRACE_GENERATED: False,
            NODE_TRACE_GENERATED: False,
        }
        
        # Graph Title
        self._title = title
        
        # Precinct Geography Constraints
        self._node_count = 0
        self._max_edge_distance = 0
        
        # Graph of Precincts
        self._graph = None
        self._graph_node_metas = []
        
        # Set up graph object for edges to be drawn on
        self._edge_trace = None
        self._node_trace = None
        self._layout = None
        
    @property
    def size(self):
        """Number of precincts in graph."""
        return self._node_count
    
    @property
    def title(self):
        """Title of Graph."""
        return self._title
    
    def _new_edge_trace(self):
        """Generate a new edge trace."""
        return go.Scatter(
            x=[],y=[],
            line=self.EDGE_STYLE,
            hoverinfo='none'
            mode='lines'
        )

    def _new_node_trace(self, mode=GEOGRAPHY):
        """Generate a new node trace (includes side bar)."""
        assert mode in self.ALLOWED_MODES, "Unknown mode: {}".format(mode)
        return go.Scatter(
            x=[], y=[], text=[],
            mode='markers',
            hoverinfo='text',
            marker=self.ALLOWED_MODES[mode]['node_trace']
        )
    
    def _new_layout(self, mode=GEOGRAPHY):
        """Generate a new graph layout."""
        assert mode in self.ALLOWED_MODES, "Unknown mode: {}".format(mode)
        {
            'title': '<br>' + self._title,
            'titlefont': {
                "size": 16
            },
            'showlegend': False,
            'hovermode': 'closest',
            'margin': {
                "b": 20,
                "l": 5,
                "r": 5,
                "t": 40
            },
            'annotations': [{
                "text": self.ALLOWED_MODES[mode]['annotation'],
                "showarrow": False,
                "xref": "paper", 
                "yref": "paper",
                "x": 0.005, 
                "y": -0.002
            }],
            'xaxis': {
                "showgrid": False, 
                "zeroline": False, 
                "showticklabels": False
            },
            'yaxis': {
                "showgrid": False, 
                "zeroline": False, 
                "showticklabels": False
            }
        }
    
    def _reset(self):
        """Set up graph objects for edges, nodes and map to be drawn on."""
        self._edge_trace = self._new_edge_trace()
        self._node_trace = self._new_node_trace()
        self._layout = self._new_node_trace()
    
    @property
    def _node_coordinates(self):
        """Return euclidean coordinates of nodes.
        Used to calculate which node "borders" another node.
        Returns
        -------
            {
                node_index: [x coordinate, y coordinate],
                ...
            }
        """
        return nx.get_node_attributes(self._graph, 'pos')
    
    @property
    def _center_node(self):
        """Retrieve the most central node."""
        min_distance = 1 
        center_node = 0
        
        for node_index, (x, y) in self._node_coordinates.items():
            distance = euclidean_distance(x, y, 0.5, 0.5)
            if distance < min_distance:
                center_node = node_index
                min_distance = distance
        
        return center_node
    
    def _draw_edge_traces(self):
        """Draw the lines between the nodes on graph object."""
        if not self._runtime_state.get(EDGE_TRACE_GENERATED):
            for first_node_index, second_node_index in self._graph.edges():
                x0, y0 = self._graph.node[first_node_index]['pos']
                x1, y1 = self._graph.node[second_node_index]['pos']
                self._edge_trace['x'] += (x0, x1, None)
                self._edge_trace['y'] += (y0, y1, None)
            self._runtime_state[EDGE_TRACE_GENERATED] = True
            
    def _draw_node_traces(self):
        """Draw the nodes on graph object."""
        if not self._runtime_state.get(NODE_TRACE_GENERATED):
            for node, (x, y) in self._node_coordinates.items():
                self._node_trace['x'] += (x,)
                self._node_trace['y'] += (y,)

            for node, adjacencies in self._graph.adjacency():
                num_adjacencies = len(adjacencies)
                # self._node_trace['marker']['color'] += (num_adjacencies,)
                self._node_trace['marker']['color'].append((num_adjacencies,))
                # self._node_trace['text'] += ('# of connections: {}'.format(num_adjacencies),)
                self._node_trace['text'].append(('# of connections: {}'.format(num_adjacencies),))
            self._runtime_state[NODE_TRACE_GENERATED] = True
