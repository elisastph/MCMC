
// clock_model.cpp
#include "../include/clock_model.hpp"
#include <cmath>
#include <fstream>

ClockModel::ClockModel(int L, int M, double T, double J)
    : L(L), M(M), T(T), J(J),
      lattice(L, std::vector<int>(L)),
      dist_site(0, L - 1),
      dist_real(0.0, 1.0)
{
    std::random_device rd;
    gen.seed(rd());
    init_lattice();
}

void ClockModel::init_lattice() {
    std::uniform_int_distribution<int> state_dist(0, M - 1);
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            lattice[i][j] = state_dist(gen);
        }
    }
}

double ClockModel::spin_dot(int m1, int m2) const {
    double angle = 2.0 * M_PI * (m1 - m2) / M;
    return std::cos(angle);
}

void ClockModel::metropolis_update() {
    int i = dist_site(gen);
    int j = dist_site(gen);
    int old_state = lattice[i][j];

    // Propose a new state different from the old one
    int new_state = old_state;
    while (new_state == old_state) {
        new_state = std::uniform_int_distribution<int>(0, M - 1)(gen);
    }

    // Compute local energy difference
    std::vector<std::pair<int, int>> neighbors = {
        { (i - 1 + L) % L, j },
        { (i + 1) % L, j },
        { i, (j - 1 + L) % L },
        { i, (j + 1) % L }
    };

    double deltaE = 0.0;
    for (const auto& [ni, nj] : neighbors) {
        int neighbor = lattice[ni][nj];
        deltaE += J * (spin_dot(new_state, neighbor) - spin_dot(old_state, neighbor));
    }

    if (deltaE <= 0.0 || dist_real(gen) < std::exp(-deltaE / T)) {
        lattice[i][j] = new_state;
    }
}

double ClockModel::compute_energy() const {
    double energy = 0.0;
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            int m = lattice[i][j];
            int right = lattice[i][(j + 1) % L];
            int down  = lattice[(i + 1) % L][j];

            energy -= J * (spin_dot(m, right) + spin_dot(m, down));
        }
    }
    return energy;
}

void ClockModel::metropolis_sweep() {
    for (int n = 0; n < L*L; ++n) {
        metropolis_update();
    }
}

double ClockModel::compute_magnetization() const {
    double mx = 0.0, my = 0.0;
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            double angle = 2.0 * M_PI * lattice[i][j] / M;
            mx += std::cos(angle);
            my += std::sin(angle);
        }
    }
    return std::sqrt(mx*mx + my*my);  // <-- no /N
}

void ClockModel::save_lattice(const std::string& filename) const {
    std::ofstream file(filename);
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            file << lattice[i][j];
            if (j < L - 1) file << ",";
        }
        file << "\n";
    }
}

void ClockModel::set_lattice(const std::vector<std::vector<int>>& new_lattice) {
    lattice = new_lattice;
}

bool ClockModel::metropolis_update_deterministic(int i, int j) {
    int old_state = lattice[i][j];
    int new_state = forced_state >= 0 ? forced_state : old_state;

    if (new_state == old_state) {
        return false; // Kein echter Vorschlag
    }

    std::vector<std::pair<int, int>> neighbors = {
        { (i - 1 + L) % L, j },
        { (i + 1) % L, j },
        { i, (j - 1 + L) % L },
        { i, (j + 1) % L }
    };

    double deltaE = 0.0;
    for (const auto& [ni, nj] : neighbors) {
        int neighbor = lattice[ni][nj];
        deltaE += J * (spin_dot(new_state, neighbor) - spin_dot(old_state, neighbor));
    }

    double r = forced_random >= 0.0 ? forced_random : dist_real(gen);
    double threshold = std::exp(-deltaE / T);

    if (deltaE <= 0.0 || r < threshold) {
        lattice[i][j] = new_state;
        return true;
    }
    return false;
}
