from typing import Optional
import pandas as pd
from mcmc_tools.analysis_utils.io import load_results
from mcmc_tools.analysis_utils.stats import compute_statistics
from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Statistic, Simulation

def analyze_and_store_latest_statistics(n_simulations: Optional[int] = None) -> int:
    """
    Lädt die neuesten Simulationen (optional begrenzt), berechnet Kennzahlen und schreibt sie in 'statistics'.
    Rückgabe: Anzahl geschriebener Zeilen.
    """
    # 1) Kandidaten ermitteln (hier einfach alle; optional: limit auf n_simulations)
    df = load_results(model=None, T=None)
    if df.empty:
        return 0

    if n_simulations:
        # crude Heuristik: letzte n_simulations Simulationen
        latest_ids = (df[["simulation_id", "model", "temperature"]]
                      .drop_duplicates("simulation_id")
                      .sort_values("simulation_id", ascending=False)
                      .head(n_simulations)["simulation_id"]
                      .tolist())
        df = df[df["simulation_id"].isin(latest_ids)]

    # 2) Statistik berechnen
    stats_df: pd.DataFrame = compute_statistics(df)

    # 3) Schreiben
    rows = stats_df.to_dict(orient="records")
    with get_session() as s:
        # Mappe model+T auf simulation_id (hier einfache Wahl: erste passende Simulation)
        sim_map = {}
        sims = s.query(Simulation).all()
        for sim in sims:
            sim_map.setdefault((sim.model, float(sim.temperature)), []).append(sim.id)

        inserted = 0
        for r in rows:
            key = (r["model"], float(r["temperature"]))
            sim_ids = sim_map.get(key, [])
            if not sim_ids:
                continue
            sim_id = sim_ids[0]
            obj = Statistic(
                simulation_id=sim_id,
                temperature=r["temperature"],
                energy_per_spin=r["energy_per_spin"],
                magnetization_per_spin=r["magnetization_per_spin"],
                heat_capacity=r["heat_capacity"],
                susceptibility=r["susceptibility"],
                error_energy=r["error_energy"],
                error_magnetization=r["error_magnetization"],
                error_cv=r["error_cv"],
                error_chi=r["error_chi"],
            )
            s.add(obj)
            inserted += 1
    return inserted
