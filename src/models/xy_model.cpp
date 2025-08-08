// xy_model.cpp
#include "../include/xy_model.hpp"
#include <cmath>
#include <fstream>
#include <iostream>

XYModel::XYModel(int L, double T, double J)
    : L(L), T(T), J(J),
      lattice(L, std::vector<double>(L)),
      dist_site(0, L - 1),
      dist_real(0.0, 1.0),
      dist_angle(0.0, 2.0 * M_PI)
{
    std::random_device rd;
    gen.seed(rd());
    init_lattice();
}

void XYModel::init_lattice() {
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            lattice[i][j] = dist_angle(gen);
            // lattice[i][j] = 0.0;  // all spins aligned (ordered state)
        }
    }
}

double XYModel::spin_dot(double phi1, double phi2) const {
    return std::cos(phi1 - phi2);
}

void XYModel::metropolis_update() {
    int i = dist_site(gen);
    int j = dist_site(gen);

    double old_phi = lattice[i][j];
    double new_phi = dist_angle(gen); // propose completely new angle

    std::vector<std::pair<int, int>> neighbors = {
        { (i - 1 + L) % L, j },
        { (i + 1) % L, j },
        { i, (j - 1 + L) % L },
        { i, (j + 1) % L }
    };

    double deltaE = 0.0;
    for (const auto& [ni, nj] : neighbors) {
        double neighbor_phi = lattice[ni][nj];
        deltaE += J * (spin_dot(new_phi, neighbor_phi) - spin_dot(old_phi, neighbor_phi));
    }

    if (deltaE <= 0.0 || dist_real(gen) < std::exp(-deltaE / T)) {
        lattice[i][j] = new_phi;
    }
}

double XYModel::compute_energy() const {
    double energy = 0.0;
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            double phi = lattice[i][j];
            double right = lattice[i][(j + 1) % L];
            double down  = lattice[(i + 1) % L][j];

            energy -= J * (spin_dot(phi, right) + spin_dot(phi, down));
        }
    }
    return energy;
}

double XYModel::compute_magnetization() const {
    double mx = 0.0, my = 0.0;
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            mx += std::cos(lattice[i][j]);
            my += std::sin(lattice[i][j]);
        }
    }
    int N = L * L;
    return std::sqrt(mx * mx + my * my) / N;
}

void XYModel::save_lattice(const std::string& filename) const {
    std::ofstream file(filename);
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            file << lattice[i][j];
            if (j < L - 1) file << ",";
        }
        file << "\n";
    }
}

void XYModel::set_lattice(const std::vector<std::vector<double>>& new_lattice) {
    lattice = new_lattice;
}

void XYModel::set_forced_angle(double angle) {
    forced_angle = angle;
}

void XYModel::set_forced_random(double value) {
    forced_random = value;
}

bool XYModel::metropolis_update(int i, int j) {
    double old_phi = lattice[i][j];
    double new_phi = (forced_angle >= 0.0) ? forced_angle : dist_angle(gen);
    double r = (forced_random >= 0.0) ? forced_random : dist_real(gen);

    std::vector<std::pair<int, int>> neighbors = {
        { (i - 1 + L) % L, j },
        { (i + 1) % L, j },
        { i, (j - 1 + L) % L },
        { i, (j + 1) % L }
    };

    double deltaE = 0.0;
    for (const auto& [ni, nj] : neighbors) {
        double neighbor_phi = lattice[ni][nj];
        deltaE += J * (cos(new_phi - neighbor_phi) - cos(old_phi - neighbor_phi));
    }
    
    double threshold = std::exp(-deltaE / T);

    std::cout << "[DEBUG] ΔE = " << deltaE
              << ", r = " << r
              << ", threshold = " << threshold << std::endl;

    if (deltaE <= 0.0 || r < threshold) {
        lattice[i][j] = new_phi;
        return true;
    }
    return false;
}
