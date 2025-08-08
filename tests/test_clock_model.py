import os 
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import clock
import numpy as np
import pytest 

def test_clock_energy_all_aligned():
    model = clock.ClockModel(2, 4, 1.0, 1.0)  # L=2, M=4
    aligned = [[0, 0],
               [0, 0]]
    model.set_lattice(aligned)
    energy = model.compute_energy()
    assert energy == -8.0  # 4 bonds × cos(0) = 1 × J = -8 total

def test_clock_magnetization_all_aligned():
    model = clock.ClockModel(2, 4, 1.0, 1.0)
    aligned = [[1, 1],
               [1, 1]]
    model.set_lattice(aligned)
    magnetization = model.compute_magnetization()
    assert abs(magnetization - 1.0) < 1e-6

def test_clock_energy_ordered():
    model = clock.ClockModel(2, 8, 1.0, 1.0)  # L=2, M=8, T=1.0, J=1.0

    ordered = [[0, 0],
               [0, 0]]
    model.set_lattice(ordered)

    # Jeder Nachbarbeitrag: cos(0) = 1 → insgesamt 8 Paare × -1 J
    expected_energy = -8.0
    assert model.compute_energy() == pytest.approx(expected_energy)

def test_clock_magnetization_ordered():
    model = clock.ClockModel(2, 8, 1.0, 1.0)

    ordered = [[0, 0],
               [0, 0]]
    model.set_lattice(ordered)

    # Alle Spins zeigen in dieselbe Richtung (Winkel = 0)
    expected_magnetization = 1.0
    assert model.compute_magnetization() == pytest.approx(expected_magnetization)

def test_clock_metropolis_rejects_favorable_flip():
    model = clock.ClockModel(3, 8, 1.0, 1.0)

    # Alle Spins auf Zustand 0
    aligned = [[0 for _ in range(3)] for _ in range(3)]
    model.set_lattice(aligned)

    model.set_forced_state(4)      # gegenüberliegend bei M = 8
    model.set_forced_random(0.9)   # zu groß für akzeptierenden Flip

    accepted = model.metropolis_update_deterministic(1, 1)
    assert accepted is True
