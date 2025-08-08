// xy_model.hpp
#pragma once

#include <vector>
#include <random>

class XYModel {
public:
    XYModel(int L, double T, double J);

    void metropolis_update();
    double compute_energy() const;
    double compute_magnetization() const;
    void save_lattice(const std::string& filename) const;
    void set_lattice(const std::vector<std::vector<double>>& new_lattice);
    void set_forced_angle(double angle);
    void set_forced_random(double value);
    bool metropolis_update(int i, int j);  // expliziter Update an fester Stelle
    
private:
    double forced_angle = -1.0;
    double forced_random = -1.0;

    int L;                                // Lattice size (LxL)
    double T;                             // Temperature
    double J;                             // Coupling constant
    std::vector<std::vector<double>> lattice; // Angle values: phi_i ∈ [0, 2π)

    std::mt19937 gen;
    std::uniform_int_distribution<int> dist_site;
    std::uniform_real_distribution<double> dist_real; // [0, 1)
    std::uniform_real_distribution<double> dist_angle; // [0, 2π)

    void init_lattice();
    double spin_dot(double phi1, double phi2) const;
};
