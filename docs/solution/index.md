# Our Solution

## Assumptions

For our purposes, for a district map to be "legal" it must fulfill the following conditions. Maps that do not fulfill these conditions are not considered a part of the solution set. Each condition can be described with a simple `true` or `false`.

- A district cannot be seperated into two parts; all precincts in a district must be directly bordering another precinct in the same district.

!!! info "Definition"
    **Solution Set**: the set of valid district maps.

For a district map to be "good", it must fulfill the following conditions. Maps that do not fulfill these conditions are still a part of the solution set. Each condition can be described with a numerical value.

- A district is geographically compact, as in the ratio between area to perimeter is maximized.
- A district represents the population fairly. For instance, if a state has $n$ districts, each state should have $1\over{n}$th of the population in each district.

## Step 1: Represent Precincts as Graph Nodes

The first step is to construct a graph, where each node represents a precinct, where an edge is placed between two nodes if they're physically bordering each other.

Let the ordered list $G$ represent the graph, where $g_i$ is the $i$th precinct in the graph.

## Step 2: Attach Meta Data to Vertexes

Each node (precinct) has meta data, specifically population and geographical compactness.

Let the ordered list $P$ represent populations, where $p_i$ describes the population of $g_i$. Similarly, let $L$ and $A$ be ordered lists containing perimeter length and total area - respectively - of each precinct defined in $G$.

!!! success "Future Expansion"
    Meta data is designed for expansion, which allows for maps to be analyzed under further lens. For instance, demographic data may be of interest.

## Step 3: Define Graph Scoring Methodology

The graph - given the meta data defined in $P$, $L$ and $A$ - is now able to be scored. A score - synonymous to energy - is defined in such a way to describe the "good"ness of $G$. 

### Compactness Score

A score describing the compactness of $G$ should ideally rate district borders with long snaking patterns poorly. This can be described as 

$$C(G) = \sum_{i=1}^{|G|} {{{l_i}^2}\over{a_i}}$$

This score encourages districts to take the shape of circles.

### Population Balance Score

$$\sigma(G)^2 = {1\over{|G| - 1}} \sum_{i = 1}^{|G|} {(p_i - \bar{p})^2}$$

### Combination

$$ \text{score}(G) = \exp{(-\alpha C(G) - \beta \sigma (G))}$$

## Step 4: Define a Random Walk

- Moving district lines
- Metropolis Algorithm

## Step 5: Determine if a Walk is Complete

- Independence
- $\chi^2$ test