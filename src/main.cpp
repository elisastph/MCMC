// main.cpp
#include <iostream>
#include <fstream>
#include <sstream>      
#include <memory>
#include <string>
#include <iomanip>
#include <cstdlib>
#include <filesystem>

#include "include/ising_model.hpp"
#include "include/clock_model.hpp"
#include "include/xy_model.hpp"

namespace fs = std::filesystem;

std::string output_dir = "results";

int main(int argc, char* argv[]) {
    // Default parameter values
    std::string model = "Ising";
    int L = 20;
    double T = 2.0;
    int steps = 10000;
    double J = 1.0;
    int interval = 100;

    // Delete folder if exists
    if (fs::exists(output_dir)) {
        fs::remove_all(output_dir);
    }

    // Create folder
    fs::create_directories(output_dir);

    // Parse command-line arguments
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--model" && i + 1 < argc) model = argv[++i];
        else if (arg == "--L" && i + 1 < argc) L = std::atoi(argv[++i]);
        else if (arg == "--T" && i + 1 < argc) T = std::atof(argv[++i]);
        else if (arg == "--steps" && i + 1 < argc) steps = std::atoi(argv[++i]);
        else if (arg == "--J" && i + 1 < argc) J = std::atof(argv[++i]);
        else if (arg == "--interval" && i + 1 < argc) interval = std::atoi(argv[++i]);
    }

    std::ostringstream filename;
    filename << "results/results_" << model << "_L" << L << "_T" << std::fixed << std::setprecision(2) << T << ".csv";
    std::ofstream output(filename.str());
    output << "step,energy,magnetization,energy_squared,magnetization_squared\n";

    if (model == "Ising") {
        auto sim = std::make_unique<IsingModel>(L, T, J);
        for (int step = 0; step < steps; ++step) {
            sim->metropolis_update();
            if (step % interval == 0) {
                double energy = sim->compute_energy();
                double magnetization = sim->compute_magnetization();
                double energy_squared = energy * energy;
                double magnetization_squared = magnetization * magnetization;

                output << step << "," << energy << "," << magnetization << ","
                        << energy_squared << "," << magnetization_squared << "\n";

            }
            if (step % 1000 == 0) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model << "_T" << std::fixed << std::setprecision(2) << T << "_" << step << ".csv";
                sim->save_lattice(lattice_filename.str());
            
                sim->save_lattice(lattice_filename.str());
            }            
        }
    }

    else if (model == "Clock") {
        const int M = 6;  // default clock states
        auto sim = std::make_unique<ClockModel>(L, M, T, J);
        for (int step = 0; step < steps; ++step) {
            sim->metropolis_update();
            if (step % interval == 0) {
                double energy = sim->compute_energy();
                double magnetization = sim->compute_magnetization();
                double energy_squared = energy * energy;
                double magnetization_squared = magnetization * magnetization;

                output << step << "," << energy << "," << magnetization << ","
                        << energy_squared << "," << magnetization_squared << "\n";
                            }
            if (step % 1000 == 0) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model << "_T" << std::fixed << std::setprecision(2) << T << "_" << step << ".csv";
                sim->save_lattice(lattice_filename.str());
            
                sim->save_lattice(lattice_filename.str());
            }                   
        }
    }

    else if (model == "XY") {
        auto sim = std::make_unique<XYModel>(L, T, J);
        for (int step = 0; step < steps; ++step) {
            sim->metropolis_update();
            if (step % interval == 0) {
                double energy = sim->compute_energy();
                double magnetization = sim->compute_magnetization();
                double energy_squared = energy * energy;
                double magnetization_squared = magnetization * magnetization;

                output << step << "," << energy << "," << magnetization << ","
                        << energy_squared << "," << magnetization_squared << "\n";

            }
            if (step % 1000 == 0) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model << "_T" << std::fixed << std::setprecision(2) << T << "_" << step << ".csv";
                sim->save_lattice(lattice_filename.str());
            
                sim->save_lattice(lattice_filename.str());
            }  
        }
    }

    else {
        std::cerr << "Unknown model: " << model << std::endl;
        return 1;
    }

    output.close();
    return 0;
}
