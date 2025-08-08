#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../include/ising_model.hpp"
#include <pybind11/stl.h>  

namespace py = pybind11;

PYBIND11_MODULE(ising, m) {
    py::class_<IsingModel>(m, "IsingModel")
        .def(py::init<int, double, double>())
        .def("compute_energy", &IsingModel::compute_energy)
        .def("compute_magnetization", &IsingModel::compute_magnetization)
        .def("save_lattice", &IsingModel::save_lattice)
        .def("set_lattice", &IsingModel::set_lattice)
        .def("set_seed", &IsingModel::set_seed)
        .def("metropolis_update", py::overload_cast<>(&IsingModel::metropolis_update))
        .def("set_forced_random", &IsingModel::set_forced_random)
        .def("metropolis_update", py::overload_cast<int, int>(&IsingModel::metropolis_update));
    
}

