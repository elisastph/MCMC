// clock_model.hpp
#pragma once

#include <vector>
#include <random>

class ClockModel {
public:
    ClockModel(int L, int M, double T, double J);

    void metropolis_update();
    double compute_energy() const;
    double compute_magnetization() const;
    void save_lattice(const std::string& filename) const;
    void set_lattice(const std::vector<std::vector<int>>& new_lattice);    
    void set_forced_state(int s) { forced_state = s; };
    void set_forced_random(double r) { forced_random = r; };
    bool metropolis_update_deterministic(int i, int j);

    
private:
    int forced_state = -1;         // -1 → deaktiviert
    double forced_random = -1.0;   // < 0 → deaktiviert
    int L;                                 // Lattice size (LxL)
    int M;                                 // Number of clock states (e.g. 6)
    double T;                              // Temperature
    double J;                              // Coupling constant
    std::vector<std::vector<int>> lattice; // Lattice values: m_i in [0, M-1]

    std::mt19937 gen;
    std::uniform_int_distribution<int> dist_site;  // For i, j
    std::uniform_real_distribution<double> dist_real; // For r in [0,1)

    void init_lattice();
    double spin_dot(int m1, int m2) const;
};

