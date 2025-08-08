import streamlit as st
import subprocess
import os
from pathlib import Path
from analysis.visualize_lattices import generate_and_display_lattice_animations

# ---- Hilfsfunktion ----
def frange(start, stop, step):
    while start <= stop:
        yield round(start, 2)
        start += step

# ---- Streamlit Konfiguration ----
st.set_page_config(page_title="MCMC Dashboard", layout="wide")
st.sidebar.title("⚙️ Simulation Settings")

# ---- Eingabefelder (Sidebar) ----
models = st.sidebar.multiselect("Choose model(s):", ["Ising", "Clock", "XY"], default=["Ising"])
L = st.sidebar.slider("Grid size L", min_value=8, max_value=64, step=8, value=16)
steps = st.sidebar.number_input("MCMC Steps", min_value=1000, step=1000, value=10000)
temp_range = st.sidebar.slider("Temperature", min_value=0.1, max_value=5.0, value=(0.5, 3.5), step=0.25)
temp_step = st.sidebar.selectbox("Temperature steps", options=[0.05, 0.1, 0.25, 0.5], index=2)

# ---- Change detection und Reset der Analyse-Flags ----
def check_and_reset(param_name, current_value):
    if param_name not in st.session_state:
        st.session_state[param_name] = current_value
    elif st.session_state[param_name] != current_value:
        st.session_state[param_name] = current_value
        # Flags zurücksetzen
        st.session_state["analysis_done"] = False
        st.session_state["slider_used"] = False

# Anwenden auf alle Parameter
check_and_reset("prev_models", models)
check_and_reset("prev_L", L)
check_and_reset("prev_steps", steps)
check_and_reset("prev_temp_range", temp_range)
check_and_reset("prev_temp_step", temp_step)
available_temperatures = [round(x, 2) for x in frange(temp_range[0], temp_range[1], temp_step)]

defaults = {
    "simulation_running": False,
    "simulation_done": False,
    "simulation_started_once": False,
    "simulation_failed": False,
    "simulation_progress": 0.0,
    "simulation_progress_final": 0.0,
    "show_sim_success": False,
    "gif_triggered": False,
    "slider_used": False,
    "gif_triggered": False,
    "gif_temp_slider": available_temperatures[0],
    "gif_expanded": True,  # Expander-Status
    "gif_temp": 0.5,        # initialer gültiger Temperaturwert
    "slider_used": False,   # wird gesetzt sobald Slider einmal aktiv war
    "simulate_clicked": False, 
    "analysis_done": False
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "gif_prev_T" not in st.session_state:
    st.session_state["gif_prev_T"] = st.session_state["gif_temp_slider"]

# soll nur angezeigt werden wenn ich den gif button drücke
if st.session_state["analysis_done"] == False:
    if st.session_state["simulation_done"] and st.session_state["slider_used"]:
        st.write("here2")
        st.subheader("🔄 Simulation is running2...")
        st.progress(st.session_state["simulation_progress_final"])
        st.success("✅ All Simulations done!")


# ---- Start Simulation Button ----
simulate_clicked = st.sidebar.button("🚀 Start Simulation", key="simulate_button")

if simulate_clicked:
    # Simulation zurücksetzen und starten
    st.session_state["simulation_running"] = True
    st.session_state["simulation_done"] = False
    st.session_state["simulation_progress"] = 0.0
    st.session_state["simulation_started_once"] = True
    st.session_state["simulation_progress_final"] = 0.0

    st.subheader("🔄 Simulation is running...")
    progress_bar = st.progress(0)
    total_tasks = len(models) * len(list(frange(temp_range[0], temp_range[1], temp_step)))
    current_task = 0

    success = True  # ← NEU

    for model in models:
        for T in frange(temp_range[0], temp_range[1], temp_step):
            cmd = [
                "../build/mcmc",
                "--model", model,
                "--L", str(L),
                "--T", str(T),
                "--steps", str(steps)
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Error for {model}, T={T:.2f}: {e.stderr.strip()}")
                success = False  # Fehler aufgetreten → Flag nicht setzen
                continue

            current_task += 1
            progress_bar.progress(current_task / total_tasks)
            st.session_state["simulation_progress"] = current_task / total_tasks
            st.session_state["simulation_progress_final"] = st.session_state["simulation_progress"]

    if success:
        st.session_state["simulation_done"] = True
        st.session_state["simulation_progress"] = 1.0
        st.session_state["simulation_progress_final"] = 1.0
        st.success("✅ All Simulations done!")
    else:
        st.warning("⚠️ Simulation teilweise fehlgeschlagen.")
        st.session_state["simulation_done"] = True
        st.session_state["simulation_progress_final"] = 1.0

    st.session_state["simulation_running"] = False

# ---- Anzeige Simulation läuft (nur bei Startbutton) ----
if st.session_state["simulation_running"]:
    st.subheader("🔄 Simulation is running...")
    st.progress(st.session_state["simulation_progress_final"])

# ---- Start Analysis Button ----
if st.session_state["simulation_done"] and st.session_state["simulation_started_once"]:
    st.markdown("---")
    st.subheader("🎞️ Analysis of systems")

    output_dir = "streamlit_app/analysis_results/visualize_lattices"
    os.makedirs(output_dir, exist_ok=True)

    # Auswahl der Temperatur für die Animation
    selected_T = st.select_slider("Choose a temperature:", options=available_temperatures, key="gif_temp_slider")

    # Button für die Analyse
    if st.button("🎞️ Start Analysis", key="start_analysis"):
        st.session_state["analysis_done"] = True
        generate_and_display_lattice_animations(
            models_selected=models,
            T_target=selected_T,
            output_dir=output_dir
        )
else:
    st.markdown("---")
    st.info("ℹ️ Start your Simulation before doing analysis.")
