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
    # Auf Quadratgitter: 2 * L * L Bindungen, cos(0)=1 -> -2*L^2 * J
    expected = -2 * L * L
    assert abs(E - expected) < 1e-6


def test_xy_energy_increases_when_spin_rotated():
    L = 3
    model = xy.XYModel(L, 0.1, 1.0)

    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    model.set_lattice(aligned)
    E_aligned = model.compute_energy()

    disturbed = [[0.0 for _ in range(L)] for _ in range(L)]
    disturbed[1][1] = np.pi  # antiparallel in der Mitte
    model.set_lattice(disturbed)
    E_disturbed = model.compute_energy()

    assert E_disturbed > E_aligned


def test_xy_magnetization_all_aligned():
    L = 4
    model = xy.XYModel(L, 0.1, 1.0)

    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    model.set_lattice(aligned)

    M = model.compute_magnetization()
    # Unnormiert: Betrag der Vektorsumme = N = L*L
    assert M == pytest.approx(L * L, abs=1e-6)


def test_xy_magnetization_reduces_with_opposite_spin():
    L = 3
    model = xy.XYModel(L, 0.1, 1.0)

    aligned = [[0.0 for _ in range(L)] for _ in range(L)]
    aligned[1][1] = np.pi  # Gegendrehung in der Mitte
    model.set_lattice(aligned)

    M = model.compute_magnetization()
    # 8 Spins bei 0 (Summe 8) + 1 Spin bei π (Summe -1) -> Betrag = 7
    expected = 7.0
    assert M == pytest.approx(expected, abs=1e-6)


def test_xy_metropolis_rejects_favorable_flip():
    model = xy.XYModel(3, 1.0, 1.0)

    lattice = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [np.pi, 0.0, 0.0],  # nur EIN Spin ist irgendwo antiparallel (kein direkter Nachbar)
    ]
    model.set_lattice(lattice)

    # Erzwinge Flip des Zentrums auf π; alle 4 Nachbarn sind bei 0 -> ΔE < 0 (günstig) -> akzeptiert
    model.set_forced_angle(np.pi)
    model.set_forced_random(0.9)

    accepted = model.metropolis_update_deterministic(1, 1)
    assert accepted is True
