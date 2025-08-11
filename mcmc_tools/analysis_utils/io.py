from typing import Optional
import pandas as pd
from sqlalchemy import select
from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Result, Simulation, Statistic
import os
from typing import List
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import streamlit as st
import plotly.graph_objects as go
def load_results(model: str, T: Optional[float] = None) -> pd.DataFrame:
    """Lädt Roh-Ergebnisse (Result + Simulation) als DataFrame."""
    with get_session() as s:
        stmt = select(
            Result.id, Result.simulation_id, Result.step,
            Result.energy, Result.magnetization, Result.energy_squared, Result.magnetization_squared,
            Simulation.model, Simulation.temperature, Simulation.lattice_size, Simulation.steps
        ).join(Simulation, Simulation.id == Result.simulation_id)
        if model:
            stmt = stmt.where(Simulation.model == model)
        if T is not None:
            stmt = stmt.where(Simulation.temperature == T)
        rows = s.execute(stmt).mappings().all()
    return pd.DataFrame(rows)

# from typing import Optional, Sequence
# import pandas as pd
# from sqlalchemy import select
# from mcmc_tools.db.connection import get_session
# from mcmc_tools.db.models import Statistic, Simulation

# from typing import Optional, Sequence
# import pandas as pd
# from sqlalchemy import select, exists
# from mcmc_tools.db.connection import get_session
# from mcmc_tools.db.models import Statistic, Simulation
# from typing import Optional, Sequence
# import pandas as pd
# from sqlalchemy import select, func
# from mcmc_tools.db.connection import get_session
# from mcmc_tools.db.models import Statistic, Simulation

# def load_statistics(
#     models: Optional[Sequence[str]] = None,
#     temperatures: Optional[Sequence[float]] = None,
#     round_temp: int = 2
# ) -> pd.DataFrame:
#     """
#     Lädt die *neuesten* Statistik-Einträge pro Simulation aus der DB.
#     Optional Filter nach Modell und Temperatur.
#     Gibt alle Spalten ohne Aggregation zurück.
#     """
#     with get_session() as s:
#         # Unterquery: neuester created_at pro Simulation
#         subq = (
#             select(
#                 Statistic.simulation_id,
#                 func.max(Statistic.created_at).label("max_created")
#             )
#             .group_by(Statistic.simulation_id)
#             .subquery()
#         )

#         stmt = (
#             select(
#                 Simulation.model.label("model"),
#                 Statistic.simulation_id,
#                 Statistic.temperature,
#                 Statistic.energy_per_spin,
#                 Statistic.magnetization_per_spin,
#                 Statistic.heat_capacity,
#                 Statistic.susceptibility,
#                 Statistic.error_energy,
#                 Statistic.error_magnetization,
#                 Statistic.error_cv,
#                 Statistic.error_chi,
#                 Statistic.created_at,
#             )
#             .join(Simulation, Simulation.id == Statistic.simulation_id)
#             .join(subq, (Statistic.simulation_id == subq.c.simulation_id) &
#                         (Statistic.created_at == subq.c.max_created))
#         )

#         rows = s.execute(stmt).mappings().all()

#     df = pd.DataFrame(rows)
#     if df.empty:
#         return df

#     # Filter anwenden
#     if models:
#         df = df[df["model"].isin(models)]

#     if temperatures:
#         temps_r = [round(float(t), round_temp) for t in temperatures]
#         df = df[df["temperature"].round(round_temp).isin(temps_r)]

#     return df.sort_values(["model", "temperature", "simulation_id"])

# --- DB ---
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

output_dir = "analysis_results/visualize_with_error"
os.makedirs(output_dir, exist_ok=True)

def _to_py_floats(temperatures: List[float]) -> List[float]:
    # np.float64 -> float und stabil auf 2 Nachkommastellen
    return [float(round(float(t), 2)) for t in temperatures]

def _fetch_last_k_stats_for_model(model: str, L: int, temperatures: List[float]) -> pd.DataFrame:
    """
    Holt für jedes gewünschte T den NEUESTEN Statistik-Eintrag (per st.id) für (model, L).
    Matched Temperaturen auf 2 Nachkommastellen.
    """
    temps_py = _to_py_floats(temperatures)
    if not temps_py:
        return pd.DataFrame()

    # Wichtig: Partitionsfenster pro T und dann nur rn=1 nehmen.
    # SQLite/Postgres/MySQL8+ können das. Für sehr alte MySQL-Versionen müssten wir subselects nehmen.
    sql = """
    WITH ranked AS (
        SELECT
            st.id AS stat_id,
            ROUND(CAST(st.temperature AS numeric), 2) AS temperature_r2,
            st.temperature AS temperature,
            st.energy_per_spin  AS energy,
            st.magnetization_per_spin AS magnetization,
            st.heat_capacity    AS cv,
            st.susceptibility   AS chi,
            st.error_energy,
            st.error_magnetization,
            st.error_cv,
            st.error_chi,
            sim.id              AS sim_id,
            sim.steps           AS steps,
            sim.lattice_size    AS L,
            ROW_NUMBER() OVER (
                PARTITION BY ROUND(CAST(st.temperature AS numeric), 2)
                ORDER BY st.id DESC
            ) AS rn
        FROM statistics st
        JOIN simulations sim ON st.simulation_id = sim.id
        WHERE sim.model = :model
        AND sim.lattice_size = :L
    )
    SELECT *
    FROM ranked
    WHERE rn = 1
    AND temperature_r2 IN :temps
    ORDER BY temperature_r2 ASC
    """
    # SQLAlchemy akzeptiert für IN-Listen meist Tuple
    params = {"model": model, "L": L, "temps": tuple(temps_py)}
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=params)
    return df
# def _to_py_floats(temperatures: List[float]) -> List[float]:
#     # np.float64 -> float und stabil auf 2 Nachkommastellen
#     return [float(round(float(t), 2)) for t in temperatures]

# def _fetch_last_k_stats_for_model(model: str, L: int, k: int) -> pd.DataFrame:
#     """
#     Holt die LETZTEN k Statistik-Einträge für ein Modell (und L),
#     anhand der statistics.id (chronologisch eingefügt).
#     Kein Filter auf steps, damit kleine Abweichungen nicht killen.
#     """
#     sql = """
#     SELECT
#         st.id                AS stat_id,
#         st.temperature      AS temperature,
#         st.energy_per_spin  AS energy,
#         st.magnetization_per_spin AS magnetization,
#         st.heat_capacity    AS cv,
#         st.susceptibility   AS chi,
#         st.error_energy,
#         st.error_magnetization,
#         st.error_cv,
#         st.error_chi,
#         sim.id              AS sim_id,
#         sim.steps           AS steps,
#         sim.lattice_size    AS L
#     FROM statistics st
#     JOIN simulations sim ON st.simulation_id = sim.id
#     WHERE sim.model = :model
#       AND sim.lattice_size = :L
#     ORDER BY st.id DESC
#     LIMIT :k
#     """
#     with engine.connect() as conn:
#         df = pd.read_sql(text(sql), conn, params={"model": model, "L": L, "k": int(k)})
#     return df

