#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../include/clock_model.hpp"

namespace py = pybind11;

PYBIND11_MODULE(clock, m) {
    py::class_<ClockModel>(m, "ClockModel")
        .def(py::init<int, int, double, double>())  // L, M, T, J
        .def("compute_energy", &ClockModel::compute_energy)
        .def("compute_magnetization", &ClockModel::compute_magnetization)
        .def("metropolis_update", &ClockModel::metropolis_update)
        .def("set_lattice", &ClockModel::set_lattice)
        .def("metropolis_update_deterministic", &ClockModel::metropolis_update_deterministic)
        .def("set_forced_state", &ClockModel::set_forced_state)
        .def("set_forced_random", &ClockModel::set_forced_random);

}
