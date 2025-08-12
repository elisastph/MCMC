# mcmc_tools/db/etl.py
from __future__ import annotations

import os
import re
import io
import base64
from typing import List, Tuple, Optional, Sequence, Set
from sqlalchemy import insert

import numpy as np
import pandas as pd

from mcmc_tools.db.connection import get_session 
from mcmc_tools.db.models import Simulation, Result, Lattice


# -------- Helpers --------

def parse_filename(filename: str) -> Tuple[str, int, float]:
    """
    Erwartet: results_<MODEL>_L<L>_T<temp>.csv
    Beispiel: results_Ising_L16_T2.50.csv
    """
    pattern = r"^results_(\w+)_L(\d+)_T([\d.]+)\.csv$"
    m = re.search(pattern, filename)
    if not m:
        raise ValueError(f"❌ Ungültiger Dateiname: {filename}")
    return m.group(1), int(m.group(2)), float(m.group(3))


def array_to_base64(arr: np.ndarray) -> str:
    """Serialisiert ein 2D-Array verlustfrei als Base64 (per np.save in Bytes)."""
    buf = io.BytesIO()
    np.save(buf, arr)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# -------- Single-file import --------

def import_simulation_with_lattices(filepath: str) -> int:
    """
    Liest eine CSV (results_...csv) + passende lattice_...csv Dateien und schreibt 1 Simulation.
    Gibt die neue Simulation-ID zurück (oder -1 bei Fehler).

    Performance-Optimierungen:
      - schnelles CSV-Parsing (usecols, dtype)
      - Bulk-Insert für 'results' (batched)
      - Bulk-Insert für 'lattices' (batched)
    """
    print(f"\n🔍 Verarbeite Datei: {filepath}")
    fname = os.path.basename(filepath)
    model, L, T = parse_filename(fname)  # erwartet results_<MODEL>_L<L>_T<temp>.csv

    # Results einlesen (schneller & sparsamer)
    try:
        df = pd.read_csv(
            filepath,
            usecols=[
                "step", "energy", "magnetization", "energy_squared", "magnetization_squared"
            ],
            dtype={
                "step": "int32",
                "energy": "float32",
                "magnetization": "float32",
                "energy_squared": "float32",
                "magnetization_squared": "float32",
            },
            engine="c",
        )
    except Exception as e:
        print(f"❌ Fehler beim Lesen von {filepath}: {e}")
        return -1

    if "step" not in df.columns:
        raise ValueError("results CSV fehlt 'step' Spalte.")

    # einheitliche Sortierung & Dubletten weg
    df = df.sort_values("step").drop_duplicates(subset=["step"])

    with get_session() as session:
        # Hinweis, falls bereits eine Simulation existiert (reine Infoausgabe)
        existing_sim = (
            session.query(Simulation)
            .filter(
                Simulation.model == model,
                Simulation.temperature == float(T),
                Simulation.lattice_size == int(L),
            )
            .order_by(Simulation.id.desc())
            .first()
        )
        if existing_sim:
            n_existing = (
                session.query(Result)
                .filter(Result.simulation_id == existing_sim.id)
                .count()
            )
            print(
                f"ℹ️ Es existiert bereits sim_id={existing_sim.id} "
                f"für (model={model}, T={T:.2f}, L={L}) mit {n_existing} Steps. "
                f"Importiere trotzdem eine NEUE Simulation."
            )

        # Neue Simulation anlegen
        sim = Simulation(
            model=model,
            temperature=float(T),
            steps=int(len(df)),
            lattice_size=int(L),
        )
        session.add(sim)
        session.flush()  # sim.id verfügbar
        print(f"➡️ Neue Simulation: ID={sim.id}, Model={model}, T={T:.2f}, L={L}, Steps={len(df)}")

        # -------- Results: BULK INSERT (batched) --------
        BATCH = 5000  # ggf. anpassen
        results_rows = [
            {
                "simulation_id": sim.id,
                "step": int(row.step),
                "energy": float(row.energy),
                "magnetization": float(row.magnetization),
                "energy_squared": float(row.energy_squared),
                "magnetization_squared": float(row.magnetization_squared),
            }
            for row in df.itertuples(index=False)
        ]

        for k in range(0, len(results_rows), BATCH):
            session.execute(insert(Result), results_rows[k : k + BATCH])
            # flush für geringeren Memory-Footprint (commit am Ende via Context-Manager)
            session.flush()

        # -------- Lattice-Dateien importieren (BULK) --------
        lattice_dir = os.path.dirname(filepath)
        t_str = f"{T:.2f}"

        # Neues Muster (mit L)
        pattern_new = rf"lattice_{re.escape(model)}_L{int(L)}_T{re.escape(t_str)}_\d+\.csv"
        lattice_files = sorted(
            f for f in os.listdir(lattice_dir) if re.fullmatch(pattern_new, f)
        )

        # Fallback: altes Muster (ohne L)
        used_pattern = "new"
        if not lattice_files:
            pattern_old = rf"lattice_{re.escape(model)}_T{re.escape(t_str)}_\d+\.csv"
            lattice_files = sorted(
                f for f in os.listdir(lattice_dir) if re.fullmatch(pattern_old, f)
            )
            used_pattern = "old"
        print(f"🧭 Lattice-Muster benutzt: {used_pattern} | Dateien gefunden: {len(lattice_files)}")

        # Vorhandene Steps in dieser Simulation (Duplikate vermeiden)
        existing_steps = set(
            r[0]
            for r in session.query(Lattice.step)
            .filter(Lattice.simulation_id == sim.id)
            .all()
        )

        lattice_rows = []
        total_lattices = 0
        skipped_shape = 0
        skipped_dupe = 0
        read_errors = 0

        for lf in lattice_files:
            m = re.search(r"_(\d+)\.csv$", lf)
            if not m:
                continue
            step = int(m.group(1))
            if step in existing_steps:
                skipped_dupe += 1
                continue

            full = os.path.join(lattice_dir, lf)
            try:
                data = np.loadtxt(full, delimiter=",")
            except Exception as e:
                print(f"⚠️  skip {lf}: read error: {e}")
                read_errors += 1
                continue

            # SHAPE-GUARD: nur (L, L) akzeptieren
            if not (isinstance(data, np.ndarray) and data.ndim == 2 and data.shape == (L, L)):
                print(f"⚠️  skip {lf}: shape {getattr(data, 'shape', None)} != ({L}, {L})")
                skipped_shape += 1
                continue

            encoded = array_to_base64(data)
            lattice_rows.append(
                {
                    "simulation_id": sim.id,
                    "model": model,
                    "temperature": float(T),
                    "step": step,
                    "data": encoded,
                }
            )
            existing_steps.add(step)
            total_lattices += 1

            # optional: auch bei Lattices batched schreiben
            if len(lattice_rows) >= BATCH:
                session.execute(insert(Lattice), lattice_rows)
                session.flush()
                lattice_rows.clear()

        # Rest flushen
        if lattice_rows:
            session.execute(insert(Lattice), lattice_rows)
            session.flush()

        print(
            f"🧩 Lattices: imported={total_lattices}, "
            f"skipped_shape={skipped_shape}, skipped_dupe={skipped_dupe}, read_errors={read_errors}"
        )

        # Commit durch Context-Manager
        return sim.id


# -------- Bulk import --------

def import_all_from_results_folder(
    folder: str = "results",
    models: Optional[Sequence[str]] = None,
    L: Optional[int] = None,
    temperatures: Optional[Sequence[float]] = None,
) -> int:
    """
    Sucht im Ordner nach 'results_*.csv' und importiert nur Dateien,
    die zu den optionalen Filtern (models, L, temperatures) passen.
    """
    print(f"\n📂 Durchsuche Ordner: {folder}")
    if not os.path.isdir(folder):
        print("⚠️ Ordner nicht gefunden.")
        return 0

    files = sorted(f for f in os.listdir(folder) if f.startswith("results_") and f.endswith(".csv"))
    if not files:
        print("⚠️ Keine results_*.csv gefunden.")
        return 0

    # Filter vorbereiten (auf 2 Nachkommastellen runden wie bei deinen Filenamen)
    models_set: Optional[Set[str]] = set(models) if models else None
    temps_set: Optional[Set[float]] = (
        set(round(float(t), 2) for t in temperatures) if temperatures else None
    )

    def _match(fname: str) -> bool:
        try:
            m, l, t = parse_filename(fname)  # (model, L, T_float)
            t = round(float(t), 2)
        except Exception:
            return False
        if models_set is not None and m not in models_set:
            return False
        if L is not None and l != L:
            return False
        if temps_set is not None and t not in temps_set:
            return False
        return True

    selected = [f for f in files if _match(f)]
    if not selected:
        print("ℹ️ Nichts passend zu den Filtern gefunden.")
        return 0

    count = 0
    for fname in selected:
        try:
            sim_id = import_simulation_with_lattices(os.path.join(folder, fname))
            if sim_id != -1:
                count += 1
        except Exception as e:
            print(f"❌ Fehler beim Import von {fname}: {e}")
    print(f"📦 Done. {count} Simulation(en) verarbeitet.")
    return count
