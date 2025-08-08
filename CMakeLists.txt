cmake_minimum_required(VERSION 3.14)
project(MCMC)

set(CMAKE_CXX_STANDARD 17)

# -------- pybind11 via FetchContent --------
include(FetchContent)

FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.12.0  # oder master, aber Version ist stabiler
)

FetchContent_MakeAvailable(pybind11)

# -------- Includes --------
include_directories(include)

# -------- Executable --------
add_executable(mcmc
    src/main.cpp
    src/models/ising_model.cpp
    src/models/clock_model.cpp
    src/models/xy_model.cpp
)

# -------- Python-Modul via pybind11 --------
pybind11_add_module(ising
    src/bindings/ising_model_bindings.cpp
    src/models/ising_model.cpp
)

pybind11_add_module(xy
    src/bindings/xy_model_bindings.cpp
    src/models/xy_model.cpp
)

pybind11_add_module(clock
    src/bindings/clock_model_bindings.cpp
    src/models/clock_model.cpp
)
