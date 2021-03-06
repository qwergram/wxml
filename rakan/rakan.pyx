# distutils: language = c++
from cython.operator import dereference, preincrement, address

from libcpp.list cimport list as clist
from libcpp.vector cimport vector as cvector

from rakan cimport Precinct as cPrecinct
from rakan cimport Rakan as cRakan

cdef class PyPrecinct:

    cdef cPrecinct __cprecinct

    def __cinit__(self, int rid=0, int district=0):
        self.__cprecinct = cPrecinct(rid, district)

    #def __dealloc__(self):
    #    del self.__cprecinct

    def __eq__(self, other):
        return other.rid == self.rid

    def __str__(self):
        return "<Rakan Precinct rid={} district={}>".format(self.__cprecinct.rid, self.__cprecinct.district)

    @property
    def rid(self):
        return self.__cprecinct.rid;

    @property
    def district(self):
        return self.__cprecinct.district;
        
    @district.setter
    def district(self, int value):
        self.__cprecinct.district = value

    @property
    def area(self):
        return self.__cprecinct.area

    @property
    def democrat_votes(self):
        return self.__cprecinct.democrat_votes

    @property
    def republican_votes(self):
        return self.__cprecinct.republican_votes

    @property
    def other_votes(self):
        return self.__cprecinct.other_votes

    @property
    def neighbors(self):
        return [PyPrecinct.factory(dereference(_)) for _ in self.__cprecinct.neighbors]

    @staticmethod
    cdef factory(cPrecinct cprecinct):
        py_obj = PyPrecinct.__new__(PyPrecinct)
        (<PyPrecinct>py_obj).__cprecinct = cprecinct
        return py_obj

cdef class PyRakan:

    cdef cRakan __crakan

    # Initialization + Destruction

    def __cinit__(self, int size = 10000, int districts = 100):
        self.__crakan = cRakan(size, districts)

    def __dealloc__(self):
        pass

    # == API for debugging in python ==

    def __len__(self) -> int:
        return self.__crakan.atlas().size()

    @property
    def districts(self) -> list:
        districts = self.__crakan.districts()
        return districts

    @property
    def precincts(self) -> list:
        c_precincts = self.__crakan.atlas()
        py_precincts = [PyPrecinct.factory(dereference(_)) for _ in c_precincts]
        return py_precincts

    @property
    def edges(self) -> list:
        edges = self.__crakan.edges()
        return edges._tree

    # == API for myself ==
    @property
    def _unchecked_changes(self) -> list:
        return self.__crakan._unchecked_changes
    
    @property
    def _checked_changes(self) -> list:
        return self.__crakan._checked_changes

    # == API for construction ==

    def add_precinct(self, int district, int population = 0) -> int:
        return self.__crakan.add_precinct(district, population)

    def set_neighbors(self, int rid1, int rid2):
        return self.__crakan.set_neighbors(rid1, rid2)

    # == API for the mathematicians ==

    def get_neighbors(self, int rid) -> dict:
        return self.__crakan.get_neighbors(rid)

    def get_diff_district_neighbors(self, int rid) -> dict:
        return self.__crakan.get_diff_district_neighbors(rid)

    def are_connected(self, int rid1, int rid2, int black_listed_rid = -1) -> bool:
        return self.__crakan.are_connected(rid1, rid2, black_listed_rid)

    def is_valid(self) -> bool:
        return self.__crakan.is_valid()

    def propose_random_move(self) -> tuple:
        return self.__crakan.propose_random_move()

    def move_precinct(self, int rid, int district):
        return self.__crakan.move_precinct(rid, district)

