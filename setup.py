from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension

ext_modules = [
    Pybind11Extension(
        "ising",
        ["src/bindings/ising_model_bindings.cpp", "src/models/ising_model.cpp"],
        include_dirs=["src"],
        cxx_std=17,
    ),
]

setup(
    name="ising",
    version="0.1",
    ext_modules=ext_modules,
    zip_safe=False,
)
