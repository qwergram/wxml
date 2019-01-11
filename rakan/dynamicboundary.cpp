#include "dynamicboundary.h"

// Simple dynamic boundary via just marking edges
// Will not be wrapped in Python.

namespace rakan {
    
    // Build a false tree
    DynamicBoundary::DynamicBoundary(int size) {
        this->_tree = false_tree(size);
    }

    // Build a false tree
    DynamicBoundary::DynamicBoundary() {
        this->_tree = false_tree();
    }


    // add a node to the tree (no edges)
    void DynamicBoundary::add_node(int rid) {
        // In python:
        // self._tree[rid] = [[], []]
        // The first list is the different district precinct neighbors
        // The second list is the same district precinct neighbors
        this->_tree[rid] = false_node();
        this->_nodes++;
    }

    // add an edge to the tree (two directional)
    // both rids must already be added to the tree via add_node
    void DynamicBoundary::add_edge(int rid1, int rid2, bool diff) {
        if (diff) { // create an edge of two precincts in different districts
            this->_d_edges += 2; // because two edges are established
            this->_tree[rid1].first.push_back(rid2);
            this->_tree[rid2].first.push_back(rid1);
        } else { // create an edge of two precincts in the same district
            this->_s_edges += 2; // because two edges are established
            this->_tree[rid1].second.push_back(rid2);
            this->_tree[rid2].second.push_back(rid1);
        }

    }

    // return a pair of rids of two neighboring precincts that are
    // are in two different districts
    std::pair<int, int> DynamicBoundary::get_random_district_edge() {
        return this->get_district_edge(rand() % this->_d_edges);
    }

    // return the nth edge of this tree
    std::pair<int, int> DynamicBoundary::get_district_edge(int index) {
        if (index >= this->_d_edges || index < 0)
            throw std::out_of_range("invalid index");
        int rid = 0;
        while (index >= (int)this->_tree[rid].first.size()) {
            index -= this->_tree[rid].first.size();
            rid++;
        }
        std::list<int>::iterator it = this->_tree[rid].first.begin();
        std::advance(it, index);
        return std::pair<int, int>(rid, *it);
    }

    // Toggles how the edges are marked in the dynamic boundary
    // If the two two nodes are marked as different-district precincts, they're marked as same-district precincts after this operation
    // Similarly, two nodes are marked as different-district precincts if they were originally different-district precincts.
    void DynamicBoundary::toggle_edge(int rid1, int rid2) {
        false_node node = this->_tree[rid1];
        false_node node2 = this->_tree[rid2];

        // is rid2 in rid1's different district neighbor list?
        if (std::find(node.first.begin(), node.first.end(), rid2) != node.first.end()) {
            node.first.remove(rid2);
            node.second.push_back(rid2);
            node2.first.remove(rid1);
            node2.second.push_back(rid1);
            this->_d_edges -= 2;
            this->_s_edges += 2;
        // is rid2 in rid1's same district neighbor list?
        } else if (std::find(node.second.begin(), node.second.end(), rid2) != node.second.end()) {
            node.second.remove(rid2);
            node.first.push_back(rid2);
            node2.second.remove(rid1);
            node2.first.push_back(rid1);
            this->_s_edges -= 2;
            this->_d_edges += 2;
        } else {
            // desired edge dne
            throw std::invalid_argument("Unable to find desired edge");
        }
    }

    // returns the number of edges
    int DynamicBoundary::edge_count() {
        return this->_d_edges + this->_s_edges;
    }

    // returns the number of nodes
    int DynamicBoundary::node_count() {
        return this->_nodes;
    }
}

