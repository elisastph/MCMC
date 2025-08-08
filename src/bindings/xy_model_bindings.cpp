#include "../include/xy_model.hpp"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

PYBIND11_MODULE(xy, m) {
    py::class_<XYModel>(m, "XYModel")
        .def(py::init<int, double, double>())
        .def("metropolis_update", static_cast<void (XYModel::*)()>(&XYModel::metropolis_update))
        .def("metropolis_update_deterministic", static_cast<bool (XYModel::*)(int, int)>(&XYModel::metropolis_update))
        .def("compute_energy", &XYModel::compute_energy)
        .def("compute_magnetization", &XYModel::compute_magnetization)
        .def("save_lattice", &XYModel::save_lattice)
        .def("set_lattice", &XYModel::set_lattice)
        .def("set_forced_angle", &XYModel::set_forced_angle)
        .def("set_forced_random", &XYModel::set_forced_random);
}
