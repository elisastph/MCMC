from typing import Optional
import pandas as pd
from mcmc_tools.analysis_utils.io import load_results
from mcmc_tools.analysis_utils.stats import compute_statistics
from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Statistic

def analyze_and_store_latest_statistics(n_simulations: Optional[int] = None,
                                        use_abs_magnetization: bool = True) -> int:
    df = load_results(model=None, T=None)
    if df.empty:
        return 0

    if n_simulations:
        latest_ids = (df[["simulation_id"]]
                      .drop_duplicates()
                      .sort_values("simulation_id", ascending=False)
                      .head(n_simulations)["simulation_id"]
                      .tolist())
        df = df[df["simulation_id"].isin(latest_ids)]

    stats_df: pd.DataFrame = compute_statistics(df, use_abs_magnetization=use_abs_magnetization)

    rows = stats_df.to_dict(orient="records")
    with get_session() as s:
        inserted = 0
        for r in rows:
            obj = Statistic(
                simulation_id=r["simulation_id"],
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
