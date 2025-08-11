// ising_model.cpp
#include "../include/ising_model.hpp"
#include <cmath>
#include <iostream>
#include <fstream>

IsingModel::IsingModel(int L, double T, double J)
    : L(L), T(T), J(J),
      lattice(L, std::vector<int>(L)),
      dist_int(0, L - 1),
      dist_real(0.0, 1.0)
{
    std::random_device rd;
    gen.seed(rd());
    init_lattice();
}

void IsingModel::init_lattice() {
    std::uniform_int_distribution<int> spin_dist(0, 1);
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            lattice[i][j] = spin_dist(gen) == 0 ? -1 : +1;
        }
    }
}

void IsingModel::metropolis_update() {
    int i = dist_int(gen);
    int j = dist_int(gen);

    int spin = lattice[i][j];
    int up    = lattice[(i - 1 + L) % L][j];
    int down  = lattice[(i + 1) % L][j];
    int left  = lattice[i][(j - 1 + L) % L];
    int right = lattice[i][(j + 1) % L];

    int neighbor_sum = up + down + left + right;
    double deltaE = 2.0 * J * spin * neighbor_sum;

    if (deltaE <= 0.0 || dist_real(gen) < std::exp(-deltaE / T)) {
        lattice[i][j] = -spin;
    }
}

void IsingModel::metropolis_sweep() {
    // Führe N = L*L Metropolis-Versuche durch → 1 Sweep
    for (int n = 0; n < L * L; ++n) {
        metropolis_update();
    }
}

double IsingModel::compute_energy() const {
    double energy = 0.0;
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            int spin = lattice[i][j];
            int right = lattice[i][(j + 1) % L];
            int down  = lattice[(i + 1) % L][j];
            energy -= J * spin * (right + down);
        }
    }
    return energy;
}

double IsingModel::compute_magnetization() const {
    double M = 0.0;
    for (const auto& row : lattice) {
        for (int s : row) {
            M += s;
        }
    }
    return M;
}

void IsingModel::save_lattice(const std::string& filename) const {
    std::ofstream file(filename);
    for (int i = 0; i < L; ++i) {
        for (int j = 0; j < L; ++j) {
            file << lattice[i][j];
            if (j < L - 1) file << ",";
        }
        file << "\n";
    }
}

void IsingModel::set_lattice(const std::vector<std::vector<int>>& new_lattice) {
    if (new_lattice.size() != L || new_lattice[0].size() != L) {
        throw std::invalid_argument("Lattice size does not match model dimensions");
    }
    lattice = new_lattice;
}

void IsingModel::set_seed(unsigned int seed) {
    gen.seed(seed);
}

void IsingModel::set_forced_random(double r) {
    forced_random = r;
}

bool IsingModel::metropolis_update(int i, int j) {
    int spin = lattice[i][j];
    int up    = lattice[(i - 1 + L) % L][j];
    int down  = lattice[(i + 1) % L][j];
    int left  = lattice[i][(j - 1 + L) % L];
    int right = lattice[i][(j + 1) % L];

    int neighbor_sum = up + down + left + right;
    double deltaE = 2.0 * J * spin * neighbor_sum;

    double r;
    if (forced_random >= 0.0) {
        r = forced_random;
    } else {
        r = dist_real(gen);
    }

    double threshold = std::exp(-deltaE / T);

    std::cout << "[DEBUG] forced_random = " << forced_random << std::endl;
    std::cout << "[DEBUG] deltaE = " << deltaE
              << ", r = " << r
              << ", threshold = " << threshold
              << std::endl;

    if (deltaE <= 0.0 || r < threshold) {
        lattice[i][j] = -spin;
        return true;
    }
    return false;
}

