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

    // // Delete folder if exists
    // if (fs::exists(output_dir)) {
    //     fs::remove_all(output_dir);
    // }

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
    
        const int burnin_sweeps = 2000;  // thermalisieren
        const int thin          = 5;    // Sweeps pro Messung
        const int samples       = steps; // steps = Anzahl Messungen
        const int lattice_every_samples = std::max(1, samples / 20);     
        // Burn-in
        for (int s = 0; s < burnin_sweeps; ++s) sim->metropolis_sweep();
    
        // Messphase: genau 'samples' Messungen
        for (int k = 0; k < samples; ++k) {
            // zwischen Messungen 'thin' Sweeps
            for (int t = 0; t < thin; ++t) sim->metropolis_sweep();
    
            double energy        = sim->compute_energy();        // TOTAL E
            double magnetization = sim->compute_magnetization(); // TOTAL M
    
            // CSV: k ist Messindex (0..samples-1)
            output << k << "," << energy << "," << magnetization << ","
                   << (energy * energy) << "," << (magnetization * magnetization) << "\n";
    
            // Lattice NACH jeder 1000. Messung (also bei 1000, 2000, ...)
            if ( (k + 1) % lattice_every_samples == 0 ) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model
                << "_L" << L
                << "_T" << std::fixed << std::setprecision(2) << T
                << "_" << (k + 1) << ".csv";

                sim->save_lattice(lattice_filename.str());
            }
        }
    }

    else if (model == "Clock") {
        const int M = 6;
        auto sim = std::make_unique<ClockModel>(L, M, T, J);
    
        const int burnin_sweeps = 2000;             // raise near critical region if needed
        const int thin          = 5;                // sweeps per measurement
        const int samples       = steps;            // UI "steps" = number of stored measurements
        const int lattice_every_samples = 500;      // dump a lattice every 500 measurements
    
        // Burn-in
        for (int s = 0; s < burnin_sweeps; ++s) sim->metropolis_sweep();
    
        // Measurement loop: exactly 'samples' rows in CSV
        for (int k = 0; k < samples; ++k) {
            for (int t = 0; t < thin; ++t) sim->metropolis_sweep();
    
            double energy        = sim->compute_energy();        // TOTAL E
            double magnetization = sim->compute_magnetization(); // TOTAL |M|
            output << k << "," << energy << "," << magnetization << ","
                   << (energy*energy) << "," << (magnetization*magnetization) << "\n";
    
            if ((k + 1) % lattice_every_samples == 0) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model
                << "_L" << L
                << "_T" << std::fixed << std::setprecision(2) << T
                << "_" << (k + 1) << ".csv";
               sim->save_lattice(lattice_filename.str());
            }
        }
    }
    
    else if (model == "XY") {
        auto sim = std::make_unique<XYModel>(L, T, J);
    
        const int burnin_sweeps = 2000;
        const int thin          = 5;
        const int samples       = steps;
        const int lattice_every_samples = 500;
    
        for (int s = 0; s < burnin_sweeps; ++s) sim->metropolis_sweep();
    
        for (int k = 0; k < samples; ++k) {
            for (int t = 0; t < thin; ++t) sim->metropolis_sweep();
    
            double energy        = sim->compute_energy();        // TOTAL E
            double magnetization = sim->compute_magnetization(); // TOTAL |M|
            output << k << "," << energy << "," << magnetization << ","
                   << (energy*energy) << "," << (magnetization*magnetization) << "\n";
    
            if ((k + 1) % lattice_every_samples == 0) {
                std::ostringstream lattice_filename;
                lattice_filename << "results/lattice_" << model
                << "_L" << L
                << "_T" << std::fixed << std::setprecision(2) << T
                << "_" << (k + 1) << ".csv";
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
