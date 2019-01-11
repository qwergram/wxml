# Algorithm Overview

## Assumptions

For our purposes, for a district map to be "legal" it must fulfill the following conditions. Maps that do not fulfill these conditions are not considered a part of the solution set. Each condition can be described with a simple `true` or `false`.

- A district cannot be separated into two parts; all precincts in a district must be directly bordering another precinct in the same district.

!!! note "Definition"
    **Solution Set**: the set of valid district maps.

For a district map to be "good", it must fulfill the following conditions. Maps that do not fulfill these conditions are still a part of the solution set. Each condition can be described with a numerical value.

- A district is geographically compact, as in the ratio between area to perimeter is maximized.
- A district represents the population fairly. For instance, if a state has $n$ districts, each state should have roughly $1\over{n}$th of the population in each district.

## Step 1: Represent Precincts as Graph Nodes

The first step is to construct a graph, where each node represents a precinct, where an edge is placed between two nodes if they're physically bordering each other.

Let the ordered list $g$ represent the graph, where $g_i$ is the $i$th precinct in the graph.

## Step 2: Attach Meta Data to Vertexes

Each node (precinct) has meta data, specifically population and geographical compactness.

Let the ordered list $p$ represent populations, where $p_i$ describes the population of $g_i$. Similarly, let $d$ be an ordered list, where $d_i$ notes which district $g_i$ is in.

!!! note "Future Expansion"
    Meta data is designed for expansion, which allows for maps to be analyzed under further lens. For instance, demographic data may be of interest.

## Step 3: Define Graph Scoring Methodology

The graph, $g$, - and given the meta data defined in $p$ and $d$ - is now able to be scored. A score is defined in such a way to describe the "good"ness of $g$.

### Compactness Score

The goal is to rate a graph with long snaking districts poorly; or create a scoring system that is maximized when the area to perimeter ratio is maximized. In $g$, an area of a district is defined by the number of nodes it contains. A perimeter, is defined by the number of edges that connect the district and different districts.

!!! info "Example: Area"
    A district's area is defined by the number of nodes in $g$ that is a part of the specified district. For instance, in the simple graph below, district `A` would have an area of 3.
    <code><pre>A---A---C
    |   |   |
    B---A---C
    |   |   |
    B---B---C</pre></code>

!!! info "Example: Perimeter"
    A district's perimeter is defined by the number of edges that connect thie district in question and another district that isn't the same district. For instance, in the simple graph below, district `A` would have a perimeter of 5.
    <code><pre>A---A---C
    |   |   |
    B---A---C
    |   |   |
    B---B---C</pre></code>

The compactness score of $g$ should ideally rate district borders with long snaking patterns poorly. Such a scoring method could be defined as the **inverse** of:

$$C(g) = \sum^{\text{districts}} {{{\text{perimeter}}^2}\over{\text{area}}}$$

!!! warning "Inversing"
    Ideally, the higher this score the more "good" $g$ is. This score encourages districts to take the shape of circles. $C(g)$ currently rates long snaking districts higher than circular districts, so when combining the scores the *inverse* of $C(g)$ must be taken.

### Population Balance Score

Population balance scores are measured in standard deviations. Given $g$ and $p$, the standard deviation of the total population is the following:

$$\sigma(g)^2 = {1\over{|g| - 1}} \sum_{i = 1}^{|G|} {(p_i - \bar{p})^2}$$

!!! warning "Inversing"
    Ideally, the lower this score the more "good" $g$ is. $\sigma(g)$ currently scores graphs with more district population variances favorably, so when combining the scores the *inverse* of $\sigma(g)$ must be taken.

### Combination

As mentioned earlier, the scoring functions $\sigma$ and $C$ must be inversed to accurately describe "good"ness of $g$. Additionally, each component of $\text{score}(g)$ is given a weight, notated as $\alpha$ and $\beta$.

$$ \text{score}(g) = \exp{(-(\alpha C(g) + \beta \sigma (g)))}$$

!!! note "The range of the score will be between 0 and 1."

## Step 4: Define a Walk

!!! note "Definition"
    Let $G$ be a graph where each edge represents some redistricting $g$.
    An edge between two edges represents one precinct on one border changing districts.

We then utilize the Metropolis Algorithm[^1] to a walk.

### Initial State

We start with a random $g$ and set $t = 0$.

!!! note
    Typically, our "random" $g$ is a one we achieved from a previous walk.

### Iteration Algorithm

We select a random new redistricting named $g'$.
This is achieved by altering one random precinct on some district borders and switching it to the other district.
Next, we calculate $\text{score}(g')$ and compare it to $\text{score}(g)$.
Let $r$ describe the ratio of the two scores, where $r = {{\text{score}(g')}\over{\text{score}(g)}}$.

!!! success "If $r > 1$:"
    Accept the new $g'$ and set $g = g'$. Increment $t$ by 1 and repeat this algorithm.

For all cases where $r \leq 1$, we define a $u$ to be a random value between $0$ and $1$.

!!! success "If $r \leq 1$ and $r \geq u$:"
    Accept the new $g'$ and set $g = g'$. Increment $t$ by 1 and repeat this algorithm.

    <small>The first check could just be skipped, and the only required comparison is $u$ and $r$, but for the sake of thoroughness it was included in the explanation.</small>

!!! failure "If $r \leq 1$ and $r \lt u$:"
    Reject $g'$ and increment $t$ by 1 and repeat this algorithm.

## Step 5: Determine if a Walk is Complete

Typically, the algorithm before will run for "a while," defining precisely when it has run "long enough" requires analysis of the sequence of redistrictings[^2]  that have been produced by the Metropolis Algorithm[^1] detailed above. When each item in the redistricting sequence is independent of the previous redistrictings (essentially, when the sequence is random), the algorithm is considered to have run "long enough".

### Defining a Statistical Test for Randomness

If we define a new sequence as a sequence of the number of land locked districts in the same order as the redistricting sequence created by the metropolis algorithm, we could perform a statistical test to see that the sequence was random. Specifically, to see that the previous item in a sequence _does not_ affect the next item in the sequence. This was done with a Chi squared test.

[^1]:
    [The Metropolis Algorithm](https://en.wikipedia.org/wiki/Metropolis–Hastings_algorithm)

[^2]:
    [Basic Definitions](/understand/index.html)