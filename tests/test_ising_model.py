import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ising

def test_energy_consistency():
    model = ising.IsingModel(4, 1.0, 1.0)
    E_before = model.compute_energy()
    for _ in range(100):
        model.metropolis_update()
    E_after = model.compute_energy()
    assert isinstance(E_after, float)
    assert abs(E_after) > 0  # grober Plausibilitätscheck

def test_magnetization_range():
    model = ising.IsingModel(4, 1.0, 1.0)
    M = model.compute_magnetization()
    max_mag = 4 * 4  # alle Spins = +1 oder -1
    assert -max_mag <= M <= max_mag

def test_checkerboard_energy():
    model = ising.IsingModel(2, 1.0, 1.0)
    checkerboard = [[1, -1],
                    [-1, 1]]
    model.set_lattice(checkerboard)
    energy = model.compute_energy()
    assert energy == 8.0

def test_all_spins_down_energy():
    model = ising.IsingModel(2, 1.0, 1.0)
    all_down = [[-1, -1],
                [-1, -1]]
    model.set_lattice(all_down)
    energy = model.compute_energy()
    assert energy == -8.0

def test_checkerboard_magnetization():
    model = ising.IsingModel(2, 1.0, 1.0)
    checkerboard = [[1, -1],
                    [-1, 1]]
    model.set_lattice(checkerboard)
    M = model.compute_magnetization()
    assert M == 0.0

def test_all_spins_down_magnetization():
    model = ising.IsingModel(2, 1.0, 1.0)
    all_down = [[-1, -1],
                [-1, -1]]
    model.set_lattice(all_down)
    M = model.compute_magnetization()
    assert M == -4.0

def test_metropolis_accepts_negative_dE():
    model = ising.IsingModel(3, 1.0, 1.0)
    model.set_seed(42)

    # Nur der zentrale Spin ist -1, alle Nachbarn +1
    lattice = [[1, 1, 1],
               [1, -1, 1],
               [1, 1, 1]]
    model.set_lattice(lattice)

    # Viele Schritte, damit mit hoher Wahrscheinlichkeit (bei Zufall) genau der mittlere Spin gewählt wird
    for _ in range(1000):
        model.metropolis_update()

    new_energy = model.compute_energy()
    assert new_energy < 0  # weil Flip akzeptiert wurde

def test_metropolis_rejects_large_positive_dE_deterministic():
    model = ising.IsingModel(3, 1.0, 1.0)

    # Zentrum +1, Nachbarn +1 ⇒ ΔE = +8 (ungünstig)
    lattice = [[1, 1, 1],
               [1, 1, 1],
               [1, 1, 1]]

    model.set_lattice(lattice)
    model.set_forced_random(0.9)  # >> exp(-8) ≈ 0.00034

    accepted = model.metropolis_update(1, 1)

    assert accepted is False

