from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "ising",
        ["src/bindings/ising_model_bindings.cpp", "src/models/ising_model.cpp"],
        include_dirs=["src"],
        cxx_std=17,
    ),
    Pybind11Extension(
        "clock",
        ["src/bindings/clock_model_bindings.cpp", "src/models/clock_model.cpp"],
        include_dirs=["src"],
        cxx_std=17,
    ),
    Pybind11Extension(
        "xy",
        ["src/bindings/xy_model_bindings.cpp", "src/models/xy_model.cpp"],
        include_dirs=["src"],
        cxx_std=17,
    ),
]

setup(
    name="mcmc_tools",
    version="0.1.0",
    packages=["mcmc_tools", "mcmc_tools.analysis", "mcmc_tools.analysis_utils", "mcmc_tools.db"],
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
