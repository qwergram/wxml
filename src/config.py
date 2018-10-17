class Config(object):
    
    class _Meta:
        abstract = True
    
    EDGE_STYLE = {
        'width': 0.5, 
        'color': GREY
    }
    
    # Modes graph data will present
    ALLOWED_MODES = {
        GEOGRAPHY: {
            "node_trace": { # Show how well a precinct is physically connected
                "showscale": True,
                "colorscale": 'YlGnBu',
                "reversescale": True,
                "color": [],
                "size": 10,
                "colorbar": {
                    "thickness": 15,
                    "title": "Neighboring Precincts",
                    "xanchor": 'left',
                    "titleside": 'right'
                },
                "line": {
                    "width": 2
                }
            },
            "annotation": "Each node is a precinct and each edge is a border between two precincts"
        }
    }