import streamlit as st
import subprocess
from analysis.visualize_lattices import generate_and_display_lattice_animations
import os
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
    "Grid size L", 8, 64, 16, step=8,
    key="L",
    on_change=reset_display_flags
)

steps = st.sidebar.number_input(
    "MCMC Steps", min_value=1000, step=1000, value=10000,
    key="steps",
    on_change=reset_display_flags
)

temp_range = st.sidebar.slider(
    "Temperature", 0.1, 5.0, (0.5,3.5), step=0.25,
    key="temp_range",
    on_change=reset_display_flags
)

temp_step = st.sidebar.selectbox(
    "Temperature steps", [0.05,0.1,0.25,0.5],
    index=2,
    key="temp_step",
    on_change=reset_display_flags
)

# ---- Initialisiere alle Session-Flags einmalig ----
for flag in [
    "simulation_running", "simulation_done",
    "show_sim_success", "simulation_progress_final",
    "slider_used", "analysis_done", "gif_triggered",
    "simulation_started_once", "simulation_analyse_once"
]:
    st.session_state.setdefault(flag, False)

# ---- Button-Click: hier startet die Simulation in DIESEM Run ----
if st.sidebar.button("🚀 Start Simulation"):
    st.session_state.simulation_started_once = True
    st.session_state.simulation_running = True
    st.session_state.simulation_analyse_once = False

    # Setze Fortschritts-Flags zurück
    st.session_state.simulation_done = False
    st.session_state.show_sim_success = False
    st.session_state.simulation_progress_final = 0.0

    # Anzeige: Simulation läuft
    st.subheader("🔄 Simulation is running...")
    progress_bar = st.progress(0)

    # Laufzeit-Variables
    total_tasks = len(models) * int((temp_range[1]-temp_range[0]) / temp_step + 1)
    current = 0
    success = True

    # Simulation-Loop
    T = temp_range[0]
    while T <= temp_range[1] + 1e-6:
        for model in models:
            cmd = [
                "../build/mcmc",
                "--model", model,
                "--L", str(L),
                "--T", f"{T:.2f}",
                "--steps", str(steps)
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Error for {model}, T={T:.2f}: {e.stderr.strip()}")
                success = False

            current += 1
            frac = current / total_tasks
            progress_bar.progress(frac)
            st.session_state.simulation_progress_final = frac
        T = round(T + temp_step, 2)

    # Simulation beendet
    st.session_state.simulation_running = False
    st.session_state.simulation_done = True
    st.session_state.show_sim_success = success

# ---- Hinweis anzeigen, wenn noch keine Simulation gestartet wurde oder Parameter geändert wurden ----
if not st.session_state.simulation_started_once and not st.session_state.simulation_running:
    st.info("▶️ Run a simulation to get lattice configurations and animations.")

# # ---- Main-Rendering nur, wenn simulation_done True ----
# if st.session_state.simulation_done:
#     if st.session_state.show_sim_success:
#         st.success("✅ All Simulations done!")
#     else:
#         st.warning("⚠️ Simulation teilweise fehlgeschlagen.")

# ---- Main-Rendering nur, wenn simulation_done True ----
if st.session_state.simulation_done:
    if st.session_state.simulation_analyse_once:
        st.subheader("🔄 Simulation is running2...")
        st.progress(1.0)

    st.session_state.simulation_analyse_once = True

    if st.session_state.show_sim_success:
        st.success("✅ All Simulations done!")
    else:
        st.warning("⚠️ Simulation teilweise fehlgeschlagen.")

    # ---- Analysis: Evolution at Fixed Temperature ----
    st.header("Analysis: Evolution at Fixed Temperature")
    # Parameter für Analyse
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
    if st.button("Show Evolution GIFs", key="analysis_button"):
        if analysis_models:
            cols = st.columns(len(analysis_models))
            for col, model in zip(cols, analysis_models):
                with col:
                    # rufe deine Funktion für genau dieses eine Modell auf
                    generate_and_display_lattice_animations(
                        models_selected=[model],
                        T_target=T_analysis,
                        output_dir=output_dir,
                        display_width=display_width
                    )
        else:
            st.warning("Please select at least one model for analysis.")

