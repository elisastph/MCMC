// ising_model.hpp
#pragma once

#include <vector>
#include <random>

class IsingModel {
public:
    IsingModel(int L, double T, double J);

    void metropolis_update();
    double compute_energy() const;
    double compute_magnetization() const;
    void save_lattice(const std::string& filename) const;
    void set_lattice(const std::vector<std::vector<int>>& new_lattice);
    void set_seed(unsigned int seed);
    bool metropolis_update(int i, int j);
    void set_forced_random(double r);


private:
    int L;                                 // Lattice size (LxL)
    double T;                              // Temperature
    double J;                              // Coupling constant
    std::vector<std::vector<int>> lattice; // Spin lattice: -1 or +1
    double forced_random = -1.0;  // default: deaktiviert

    std::mt19937 gen;                     // RNG engine
    std::uniform_int_distribution<int> dist_int;     // Site index dist
    std::uniform_real_distribution<double> dist_real; // [0, 1) dist

    void init_lattice();
};

