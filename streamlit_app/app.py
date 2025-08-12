# app.py
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import text, inspect

# ---- App config ----
st.set_page_config(page_title="MCMC Dashboard", layout="wide")

# ---- Pfade & Binary via Helper (einheitlich für Cloud & ECS) ----
# Erstelle eine Datei binary_provider.py wie vorgeschlagen (get_mcmc_path, get_paths)
from binary_provider import get_mcmc_path, get_paths

paths = get_paths()
DATA_DIR     = paths["DATA_DIR"]
BIN_DIR      = paths["BIN_DIR"]
RESULTS_DIR  = paths["RESULTS_DIR"]
ANALYSIS_DIR = paths["ANALYSIS_DIR"]
for p in (BIN_DIR, RESULTS_DIR, ANALYSIS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ---- Projektspezifische Imports ----
from infos import (
    render_models_intro,
    render_analysis_intro,
    render_gif_snippet,
    render_plot_snippet,
)
from mcmc_tools.db.models import Base  # enthält Simulation, Result, Lattice, Statistic
from mcmc_tools.db import get_engine, get_session, healthcheck
from mcmc_tools.db.etl import import_all_from_results_folder
from mcmc_tools.analysis_utils.visualize_lattices import (
    generate_and_display_lattice_animations,
)
from mcmc_tools.analysis_utils.stat_runner import analyze_and_store_latest_statistics
from mcmc_tools.analysis_utils.plots import plot_with_errorbars


# =========================
# Helpers & Setup
# =========================

def load_config(keys=("DATABASE_URL", "SAFE_MODE")):
    # ENV aus st.secrets nur setzen, wenn noch nicht vorhanden
    for k in keys:
        if os.getenv(k):
            continue
        try:
            if k in st.secrets and st.secrets[k]:
                os.environ[k] = str(st.secrets[k])
        except Exception:
            pass

load_config()
load_dotenv()

SAFE = str(os.getenv("SAFE_MODE", "0")).lower() in {"1", "true", "yes"}

# Sanfte Limits in der Cloud
MAX_STEPS = 20_000 if SAFE else 100_000
MAX_L     = 32     if SAFE else 128

@st.cache_resource
def _engine_cached():
    return get_engine()

engine = _engine_cached()

if os.getenv("INIT_DB", "0") in {"1", "true", "yes"}:
    Base.metadata.create_all(engine)

def ensure_schema():
    insp = inspect(engine)
    want = {"simulations", "results", "lattices", "statistics"}
    have = set(insp.get_table_names())
    missing = sorted(want - have)
    if missing:
        Base.metadata.create_all(engine)
    return missing

def get_available_temperatures_and_models():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT model, temperature
            FROM simulations
            ORDER BY model, temperature
        """)).fetchall()
    return result

# ---- Helper: räumt alles weg, was rechts angezeigt wird ----
def reset_display_flags():
    for flag in [
        "simulation_running",
        "simulation_done",
        "show_sim_success",
        "simulation_progress_final",
        "slider_used",
        "analysis_done",
        "gif_triggered",
        "simulation_started_once",
        "simulation_analyse_once",
    ]:
        st.session_state[flag] = False


# =========================
# UI – Sidebar
# =========================

st.sidebar.title("⚙️ Simulation Settings")

models = st.sidebar.multiselect(
    "Choose model(s):", ["Ising", "Clock", "XY"],
    default=["Ising"],
    key="models",
    on_change=reset_display_flags,
)

L = st.sidebar.slider(
    "Grid size L", 8, MAX_L, 16, step=8,
    key="L",
    on_change=reset_display_flags,
)

steps = st.sidebar.number_input(
    "MCMC Steps",
    min_value=1000, step=1000, value=10_000,
    max_value=MAX_STEPS,
    key="steps",
    on_change=reset_display_flags,
)

temp_range = st.sidebar.slider(
    "Temperature", 0.1, 5.0, (0.5, 3.5), step=0.1,
    key="temp_range",
    on_change=reset_display_flags,
)

temp_step = st.sidebar.selectbox(
    "Temperature steps", [0.1, 0.25, 0.5, 0.75, 1.0],
    index=2,
    key="temp_step",
    on_change=reset_display_flags,
)
temp_step_val = st.session_state["temp_step"]

# ---- Initialisiere alle Session-Flags einmalig ----
for flag in [
    "simulation_running", "simulation_done",
    "show_sim_success", "simulation_progress_final",
    "slider_used", "analysis_done", "gif_triggered",
    "simulation_started_once", "simulation_analyse_once",
]:
    st.session_state.setdefault(flag, False)

if not st.session_state.get("simulation_started_once", False):
    render_models_intro()

if SAFE:
    st.sidebar.info(
        "SAFE mode: running new simulations is disabled in the cloud.\n"
        "You can still visualize and analyze existing results."
    )


# =========================
# Simulation starten
# =========================

start_pressed = st.sidebar.button("🚀 Start Simulation", disabled=SAFE)

if start_pressed and not SAFE:
    # Holt entweder den vorinstallierten Binary (MCMC_PATH) oder lädt das Release-Asset
    mcmc_path = get_mcmc_path()

    st.session_state.simulation_started_once = True
    st.session_state.simulation_running = True
    st.session_state.simulation_analyse_once = False

    st.session_state.simulation_done = False
    st.session_state.show_sim_success = False
    st.session_state.simulation_progress_final = 0.0

    st.subheader("🔄 Simulation is running...")
    progress_bar = st.progress(0)

    temperatures = np.arange(temp_range[0], temp_range[1] + temp_step_val / 2, temp_step_val)
    temperatures = [round(float(T), 2) for T in temperatures]
    total_tasks = max(1, len(models) * len(temperatures))

    current = 0
    success = True

    # Wichtig: cwd = DATA_DIR, damit das Binary in DATA_DIR/results schreibt
    for T in temperatures:
        for model in models:
            cmd = [
                str(mcmc_path),
                "--model", model,
                "--L", str(L),
                "--T", f"{T:.2f}",
                "--steps", str(steps),
            ]
            try:
                completed = subprocess.run(
                    cmd, check=True, capture_output=True, text=True,
                    cwd=str(DATA_DIR)
                )
                # Debug-Ausgabe optional
                # st.write(completed.stdout)
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Error for {model}, T={T:.2f}: {e.stderr.strip()}")
                success = False

            current += 1
            frac = current / total_tasks
            progress_bar.progress(frac)
            st.session_state.simulation_progress_final = frac

    st.session_state.simulation_running = False
    st.session_state.simulation_done = True
    st.session_state.show_sim_success = success

    # ---- Neue Ergebnisse in DB importieren ----
    n_simulations = len(models) * len(temperatures)
    import_all_from_results_folder(
        folder=str(RESULTS_DIR),  # <— wichtig: nicht ins Repo schreiben
        models=models,
        L=L,
        temperatures=temperatures,
    )
    analyze_and_store_latest_statistics(n_simulations)

    st.success("✅ Simulation, Import & Statistics done")


# =========================
# Analysebereich
# =========================

if st.session_state.simulation_done:
    render_analysis_intro()

    st.header("Analysis: Evolution at Fixed Temperature")
    analysis_models = st.multiselect(
        "Select Model(s)", models,
        default=[models[0]] if models else [],
        key="analysis_models",
    )

    T_analysis = st.slider(
        "Temperature for Analysis",
        float(temp_range[0]), float(temp_range[1]),
        float((temp_range[0] + temp_range[1]) / 2),
        step=float(temp_step),
        key="T_analysis",
    )

    display_width = 500
    render_gif_snippet()
    if st.button("Show Evolution GIFs", key="analysis_button"):
        if analysis_models:
            ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
            generate_and_display_lattice_animations(
                analysis_models, T_analysis, str(ANALYSIS_DIR), display_width=display_width
            )
        else:
            st.warning("Please select at least one model for analysis.")

    # Temperaturen aus aktuellem Simulation-Setup
    temperatures = np.arange(temp_range[0], temp_range[1] + temp_step_val / 2, temp_step_val)
    temperatures = [round(float(T), 2) for T in temperatures]

    render_plot_snippet()
    if st.button("Generate Plots with Errorbars"):
        plot_with_errorbars(analysis_models, L, steps, temperatures)


# =========================
# (Optional) Diagnostics
# =========================
# from mcmc_tools.db.models import Simulation
# with st.expander("🔧 Diagnostics", expanded=False):
#     st.write({"SAFE_MODE": os.getenv("SAFE_MODE", "0")})
#     st.write("DB:", "✅ OK" if healthcheck() else "❌ FAIL")
#     try:
#         with get_session() as s:
#             n_sim = s.query(Simulation).count()
#         st.write(f"Simulations in DB: {n_sim}")
#     except Exception as e:
#         st.write(f"DB query error: {e}")
#     st.write({"DATA_DIR": str(DATA_DIR), "RESULTS_DIR": str(RESULTS_DIR), "BIN_DIR": str(BIN_DIR)})
#     if st.button("Clear cache & reload"):
#         st.cache_data.clear()
#         st.cache_resource.clear()
#         st.rerun()
#     if st.button("Initialize DB schema (create tables)"):
#         try:
#             missing = ensure_schema()
#             if missing:
#                 st.success(f"Created tables: {missing}")
#             else:
#                 st.info("Schema already up-to-date ✔️")
#         except Exception as e:
#             st.error(f"Schema init failed: {e}")
