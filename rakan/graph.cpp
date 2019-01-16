#include "graph.h"
#include <stdio.h>

namespace rakan {
    // Simple Precinct Class. Not declared as a struct for potential expansions.
    Precinct::Precinct(int rid, int district) 
        : rid(rid), district(district) { };
    Precinct::Precinct(int rid, int district, std::list<Precinct*> neighbors)
        : rid(rid), district(district), neighbors(neighbors) { };
    
    Rakan::Rakan() {
        this->_atlas = Atlas();
        this->_edges = DynamicBoundary();
        this->_districts = Districts();
    }

    // Rakan Class.
    Rakan::Rakan(int size, int districts) {
        this->_atlas = Atlas();
        this->_atlas.reserve(size);
        this->_edges = DynamicBoundary(size);
        this->_districts = Districts(districts);
    };

    // == API FOR DEBUGGING IN PYTHON ==

    Districts Rakan::districts() {
        return this->_districts;
    }

    Atlas Rakan::atlas() {
        return this->_atlas;
    }

    DynamicBoundary Rakan::edges() {
        return this->_edges;
    }

    // == API FOR CONSTRUCTION ==

    // add a precinct with specified district
    int Rakan::add_precinct(int district, int population) {
        int new_rid = this->_atlas.size();

        // update atlas
        this->_atlas.push_back(new Precinct(new_rid, district));
        this->_atlas[new_rid]->population = population;

        // update dynamic boundary
        this->_edges.add_node(new_rid);
        
        // update district table
        this->_districts[district].push_back(new_rid);

        // add to unchecked changes
        this->_unchecked_changes.push_back(new_rid);

        return new_rid;
    }

    Rakan::~Rakan() {
        for (Precinct * a : this->_atlas) {
            delete a;
        }
    }

    // set two precincts to be neighbors. Requires precincts to have been added to district.
    void Rakan::set_neighbors(int rid1, int rid2) {
        // get precincts
        Precinct * precinct1 = this->_atlas[rid1];
        Precinct * precinct2 = this->_atlas[rid2];

        // update atlas
        precinct1->neighbors.push_back(precinct2);
        precinct2->neighbors.push_back(precinct1);

        // update dynamic boundary
        this->_edges.add_edge(rid1, rid2, precinct1->district != precinct2->district);

        // add to _unchecked_changes. Only need to be done once.
        this->_unchecked_changes.push_back(rid1);
    }

    // == API FOR NERDS ==
    
    // get the neighbors of the given rid
    // Returned as a map where {district: [rids], district: [rids], ..}
    std::map<int, std::list<int>> Rakan::get_neighbors(int rid) {
        if (rid > (int)this->_atlas.size() || rid < 0)
            throw std::out_of_range("Specified RID not found");
        std::map<int, std::list<int>> neighbors;
        for (Precinct * neighbor : this->_atlas[rid]->neighbors) {
            neighbors[neighbor->district].push_back(neighbor->rid);
        }
        return neighbors;
    }

    // get the neighbors of different districts for the given rid
    std::map<int, std::list<int>> Rakan::get_diff_district_neighbors(int rid) {
        if (rid > (int)this->_atlas.size() || rid < 0)
            throw std::out_of_range("Specified RID not found");
        std::map<int, std::list<int>> neighbors;
        int bad_district = this->_atlas[rid]->district;
        for (Precinct * neighbor : this->_atlas[rid]->neighbors) {
            if (neighbor->district != bad_district)
                neighbors[neighbor->district].push_back(neighbor->rid);
        }
        return neighbors;
    }

    // are the two precincts connected via the same district path?
    // Will not use the black_listed_rid as part of path
    bool Rakan::are_connected(int rid1, int rid2, int black_listed_rid = -1) {
        if (this->_atlas[rid1]->district != this->_atlas[rid2]->district)
            throw std::invalid_argument("Districts between selected precincts are different");
        else if (rid1 == black_listed_rid || rid2 == black_listed_rid)
            throw std::invalid_argument("Cannot blacklist the precinct that is undergoing the connectivitiy test");

        // allowed district
        int district = this->_atlas[rid1]->district;
        
        // track all possible paths
        std::vector<bool> pool = std::vector<bool>(this->_atlas.size());
        
        // set up both queues
        std::list<int> rid1queue = { rid1 };
        std::list<int> rid2queue = { rid2 };

        int cursor1, cursor2;

        while (!rid1queue.empty() || !rid2queue.empty()) {
            cursor1 = rid1queue.front();
            cursor2 = rid2queue.front();
            rid1queue.pop_front();
            rid2queue.pop_front();

            if (cursor1 != black_listed_rid) {
                if (pool[cursor1])
                    return true;
                pool[cursor1] = true;

                for (Precinct * neighbor : this->_atlas[cursor1]->neighbors) {
                    if (neighbor->district == district)
                        rid1queue.push_back(neighbor->rid);
                }
            }

            if (cursor2 != black_listed_rid) {
                if (pool[cursor2])
                    return true;
                pool[cursor2] = true;

                for (Precinct * neighbor : this->_atlas[cursor2]->neighbors) {
                    if (neighbor->district == district)
                        rid2queue.push_back(neighbor->rid);
                }
            }
        }

        return false;
    }

    // is the graph still valid?
    bool Rakan::is_valid() {
        if (!this->_unchecked_changes.empty())
            return this->_is_valid();
        return this->__is_valid;
    }

    // Propose a random move
    // all edges involving two different districted precincts are equally likely to be proposed
    // Move proposed as pair integers, where the first integer is the rid
    // and the second integer is the district number to convert it to.
    std::pair<int, int> Rakan::propose_random_move() {
        std::pair<int, int> random_rids = this->_edges.get_random_district_edge();
        return std::pair<int, int>(random_rids.first, this->_atlas[random_rids.second]->district);
    }

    // move the specified rid to the new district
    // if the move is illegal, exceptions will be thrown
    void Rakan::move_precinct(int rid, int district) {
        if (!this->is_valid())
            throw std::logic_error("Cannot make move when graph is invalid");
        if (!this->_is_legal_new_district(rid, district))
            throw std::invalid_argument("Illegal Move (Reason: No neighbors have this district)");
        if (this->_severs_neighbors(rid))
            throw std::invalid_argument("Illegal Move (Reason: Severs the neighboring district(s))");
        
        // update this->_districts
        this->_update_districts(rid, district);

        // update dynamic boundary
        this->_update_district_boundary(rid, district);

        // update atlas
        this->_update_atlas(rid, district);

        // add to checked changes
        this->_checked_changes.push_back(rid);
    }

    // return a set of rid pairs that need are_connected checks given that the 
    // passed in rid is switching districts
    std::set<std::pair<int, int>> Rakan::_checks_required(int rid) {
        int first, second;
        std::set<std::pair<int, int>> to_check;
        std::map<int, std::list<int>> pool = this->get_neighbors(rid);

        for (auto it = pool.begin(); it != pool.end(); ++it) {
            auto it2 = it->second.begin();
            first = *it2;
            for (it2++; it2 != it->second.end(); it2++) {
                second = *it2;
                to_check.insert(std::pair<int, int>(first, second));
            }
        }
        return to_check;
    }

    // perform checks if there are unchecked changes
    bool Rakan::_is_valid() {
        while (!this->_unchecked_changes.empty()) {
            int rid = this->_unchecked_changes.front();
            this->_unchecked_changes.pop_front();
            std::set<std::pair<int, int>> pool = this->_checks_required(rid);
            for (std::pair<int, int> item : pool) {
                if (!this->are_connected(item.first, item.second)) {
                    this->__is_valid = false;
                    return false;
                }
                this->_checked_changes.push_back(rid);
            }
        }
        this->__is_valid = true;
        return true;
    }

    // is it legal to attain this new district?
    // Checks that at least one neighbor shares this district
    bool Rakan::_is_legal_new_district(int rid, int district) {
        Precinct precinct = *(this->_atlas[rid]);

        if (precinct.district == district)
            return true;
        
        for (Precinct * neighbor : precinct.neighbors)
            if (neighbor->district == district)
                return true;

        return false;
    }

    // Check all the neighbors are still connected one way or another.
    bool Rakan::_severs_neighbors(int rid) {
        std::set<std::pair<int, int>> checks = this->_checks_required(rid);
        for (std::pair<int, int> item : checks)
            if (!this->are_connected(item.first, item.second, rid))
                return true;
        return false;
    }

    // update the dynamic boundary tree
    void Rakan::_update_district_boundary(int rid, int district) {
        for (Precinct * neighbor : this->_atlas[rid]->neighbors)
            if (neighbor->district == district || neighbor->district == this->_atlas[rid]->district)
                this->_edges.toggle_edge(rid, neighbor->rid);
    }

    // update the atlas
    void Rakan::_update_atlas(int rid, int district) {
        this->_atlas[rid]->district = district;
    }

    // update district map
    void Rakan::_update_districts(int rid, int district) {
        this->_districts[this->_atlas[rid]->district].remove(rid);
        this->_districts[district].push_back(rid);
    }
}