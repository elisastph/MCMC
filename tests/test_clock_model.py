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
    # 4 horizontale + 4 vertikale Bindungen, cos(0)=1 -> -8 * J
    assert energy == -8.0


def test_clock_magnetization_all_aligned():
    L = 2
    model = clock.ClockModel(L, 4, 1.0, 1.0)
    aligned = [[1, 1],
               [1, 1]]
    model.set_lattice(aligned)
    magnetization = model.compute_magnetization()
    # Unnormiert: Betrag der Vektorsumme = N = L*L = 4
    assert magnetization == pytest.approx(L * L, rel=0, abs=1e-6)


def test_clock_energy_ordered():
    model = clock.ClockModel(2, 8, 1.0, 1.0)  # L=2, M=8
    ordered = [[0, 0],
               [0, 0]]
    model.set_lattice(ordered)
    # Jeder Nachbarbeitrag: cos(0) = 1 → insgesamt 8 Paare × -1 J
    expected_energy = -8.0
    assert model.compute_energy() == pytest.approx(expected_energy)


def test_clock_magnetization_ordered():
    L = 2
    model = clock.ClockModel(L, 8, 1.0, 1.0)
    ordered = [[0, 0],
               [0, 0]]
    model.set_lattice(ordered)
    # Unnormiert: alle Spins gleich → Betrag der Summe = N
    expected_magnetization = L * L
    assert model.compute_magnetization() == pytest.approx(expected_magnetization, abs=1e-6)


def test_clock_metropolis_rejects_favorable_flip():
    model = clock.ClockModel(3, 8, 1.0, 1.0)

    # Alle Spins auf Zustand 0
    aligned = [[0 for _ in range(3)] for _ in range(3)]
    model.set_lattice(aligned)

    model.set_forced_state(4)      # gegenüberliegend bei M=8 (π)
    model.set_forced_random(0.9)   # irrelevant bei ΔE < 0, sollte akzeptiert werden

    accepted = model.metropolis_update_deterministic(1, 1)
    assert accepted is True
