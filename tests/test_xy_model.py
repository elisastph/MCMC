import os 
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import xy
import pytest
import numpy as np

@pytest.mark.parametrize("L", [2, 4, 8])
def test_xy_energy_all_aligned(L):
    model = xy.XYModel(L, 0.1, 1.0)
    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    model.set_lattice(aligned)

    E = model.compute_energy()
    expected = -2 * L * L

    assert abs(E - expected) < 1e-6

def test_xy_energy_increases_when_spin_rotated():
    L = 3
    model = xy.XYModel(L, 0.1, 1.0)

    # Alle Spins = 0
    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    model.set_lattice(aligned)
    E_aligned = model.compute_energy()

    # Drehung des mittleren Spins auf π
    disturbed = [[0.0 for _ in range(L)] for _ in range(L)]
    disturbed[1][1] = np.pi
    model.set_lattice(disturbed)
    E_disturbed = model.compute_energy()

    assert E_disturbed > E_aligned

def test_xy_magnetization_all_aligned():
    L = 4
    model = xy.XYModel(L, 0.1, 1.0)

    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    model.set_lattice(aligned)

    M = model.compute_magnetization()
    assert abs(M - 1.0) < 1e-6

def test_xy_magnetization_reduces_with_opposite_spin():
    L = 3
    model = xy.XYModel(L, 0.1, 1.0)

    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    aligned[1][1] = np.pi  # Gegendrehung in der Mitte
    model.set_lattice(aligned)

    M = model.compute_magnetization()
    expected = 7 / 9
    assert abs(M - expected) < 1e-6

def test_xy_metropolis_rejects_favorable_flip():
    model = xy.XYModel(3, 1.0, 1.0)

    lattice = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [np.pi, 0.0, 0.0],  # nur EIN Nachbar ist antiparallel
    ]
    model.set_lattice(lattice)

    model.set_forced_angle(np.pi)
    model.set_forced_random(0.9)

    accepted = model.metropolis_update_deterministic(1, 1)
    assert accepted is True
