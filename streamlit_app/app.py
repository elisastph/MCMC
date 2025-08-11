import streamlit as st
import subprocess
import os
import shutil
import numpy as np
from sqlalchemy import text
from dotenv import load_dotenv
import streamlit as st
from infos import render_models_intro, render_analysis_intro, render_gif_snippet, render_plot_snippet
import os, subprocess, pathlib

from mcmc_tools.db import get_engine, get_session, healthcheck
from mcmc_tools.db.etl import import_all_from_results_folder

from mcmc_tools.analysis_utils.visualize_lattices import (
    load_lattices_for_model_and_temperature,
    generate_and_display_lattice_animations,
)
from mcmc_tools.analysis_utils.stat_runner import analyze_and_store_latest_statistics
from mcmc_tools.analysis_utils.plots import plot_with_errorbars

for key in ("DATABASE_URL", "SAFE_MODE"):
    if key in st.secrets and st.secrets[key]:
        os.environ[key] = str(st.secrets[key])

load_dotenv()

SAFE = str(os.getenv("SAFE_MODE", "0")).lower() in {"1", "true", "yes"}

# Sanfte Limits in der Cloud
MAX_STEPS = 20_000 if SAFE else 100_000
MAX_L     = 32     if SAFE else 128

def ensure_mcmc_binary():
    build_dir = pathlib.Path("build")
    exe = build_dir / "mcmc"
    if exe.exists():
        return
    build_dir.mkdir(exist_ok=True)
    # Build only if missing
    subprocess.run(["cmake", ".."], cwd=build_dir, check=True)
    subprocess.run(["make", "-j"], cwd=build_dir, check=True)


@st.cache_resource
def _engine_cached():
    return get_engine()

engine = _engine_cached()

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
        "simulation_analyse_once"
    ]:
        st.session_state[flag] = False

# ---- Streamlit Konfig ----
st.set_page_config(page_title="MCMC Dashboard", layout="wide")
st.sidebar.title("⚙️ Simulation Settings")

# ---- Sidebar mit on_change ----
models = st.sidebar.multiselect(
    "Choose model(s):", ["Ising","Clock","XY"],
    default=["Ising"],
    key="models",
    on_change=reset_display_flags
)

L = st.sidebar.slider(
    "Grid size L", 8, MAX_L, 16, step=8,   # <- limit
    key="L",
    on_change=reset_display_flags
)

steps = st.sidebar.number_input(
    "MCMC Steps",
    min_value=1000, step=1000, value=10_000,
    max_value=MAX_STEPS,  # <- limit
    key="steps",
    on_change=reset_display_flags
)
temp_range = st.sidebar.slider(
    "Temperature", 0.1, 5.0, (0.5,3.5), step=0.1,
    key="temp_range",
    on_change=reset_display_flags
)

temp_step = st.sidebar.selectbox(
    "Temperature steps", [0.1,0.25,0.5,0.75,1.0],
    index=2,
    key="temp_step",
    on_change=reset_display_flags
)
temp_step_val = st.session_state["temp_step"]

# ---- Initialisiere alle Session-Flags einmalig ----
for flag in [
    "simulation_running", "simulation_done",
    "show_sim_success", "simulation_progress_final",
    "slider_used", "analysis_done", "gif_triggered",
    "simulation_started_once", "simulation_analyse_once"
]:
    st.session_state.setdefault(flag, False)

if not st.session_state.get("simulation_started_once", False):
    render_models_intro()


if SAFE:
    st.sidebar.info("SAFE mode: running new simulations is disabled in the cloud.\n"
                    "You can still visualize and analyze existing results.")

start_pressed = st.sidebar.button("🚀 Start Simulation", disabled=SAFE)
# ---- Simulation starten ----
if start_pressed and not SAFE:
    ensure_mcmc_binary()

    st.session_state.simulation_started_once = True
    st.session_state.simulation_running = True
    st.session_state.simulation_analyse_once = False

    st.session_state.simulation_done = False
    st.session_state.show_sim_success = False
    st.session_state.simulation_progress_final = 0.0

    st.subheader("🔄 Simulation is running...")
    progress_bar = st.progress(0)

    temperatures = np.arange(temp_range[0], temp_range[1] + temp_step_val / 2, temp_step_val)
    temperatures = [round(T, 2) for T in temperatures]  # optional, damit gleiche Formatierung
    total_tasks = len(models) * len(temperatures)

    current = 0
    success = True
    
    for T in temperatures:
        for model in models:
            cmd = [
                "build/mcmc",
                "--model", model,
                "--L", str(L),
                "--T", f"{T:.2f}",
                "--steps", str(steps)
            ]
            try:
                print(T, model)
                subprocess.run(cmd, check=True, capture_output=True, text=True)
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
        folder="results",
        models=models,
        L=L,
        temperatures=temperatures,   
    )
    analyze_and_store_latest_statistics(n_simulations)      

    st.success("✅ Simulation, Import & Statistics done")

# ---- Analysebereich ----
if st.session_state.simulation_done:
    render_analysis_intro()  

    st.header("Analysis: Evolution at Fixed Temperature")
    analysis_models = st.multiselect(
        "Select Model(s)", models,
        default=[models[0]] if models else [],
        key="analysis_models"
    )
    T_analysis = st.slider(
        "Temperature for Analysis",
        float(temp_range[0]), float(temp_range[1]),
        float((temp_range[0]+temp_range[1])/2),
        step=float(temp_step),
        key="T_analysis"
    )

    output_dir = "analysis_results/visualize_lattice"
    os.makedirs(output_dir, exist_ok=True)
        
    display_width = 500
    render_gif_snippet()
    if st.button("Show Evolution GIFs", key="analysis_button"):
        if analysis_models:
            generate_and_display_lattice_animations(
                analysis_models, T_analysis, output_dir, display_width=display_width
            )
        else:
            st.warning("Please select at least one model for analysis.")

    # Temperaturen aus aktuellem Simulation-Setup
    temperatures = np.arange(temp_range[0], temp_range[1] + temp_step_val / 2, temp_step_val)
    temperatures = [round(float(T), 2) for T in temperatures]

    render_plot_snippet()
    if st.button("Generate Plots with Errorbars"):
        plot_with_errorbars(analysis_models, L, steps, temperatures)
