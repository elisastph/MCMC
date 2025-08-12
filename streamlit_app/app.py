import streamlit as st
import os, pathlib, hashlib, tarfile, urllib.request

st.set_page_config(page_title="MCMC Dashboard", layout="wide")

OWNER   = os.getenv("MCMC_RELEASE_OWNER", "elisastph")
REPO    = os.getenv("MCMC_RELEASE_REPO",  "MCMC")
TAG     = os.getenv("MCMC_RELEASE_TAG",   "v0.1.2")
ASSET   = os.getenv("MCMC_RELEASE_ASSET", "mcmc-linux-x86_64.tar.gz")
SHA256  = os.getenv("MCMC_RELEASE_SHA256", "")

RELEASE_URL = f"https://github.com/{OWNER}/{REPO}/releases/download/{TAG}/{ASSET}"

from sqlalchemy import text, inspect
import shutil
import numpy as np
from dotenv import load_dotenv
from infos import render_models_intro, render_analysis_intro, render_gif_snippet, render_plot_snippet
import os, subprocess, pathlib, sys
from mcmc_tools.db.models import Base  # enthält Simulation, Result, Lattice, Statistic

from mcmc_tools.db import get_engine, get_session, healthcheck
from mcmc_tools.db.etl import import_all_from_results_folder

from mcmc_tools.analysis_utils.visualize_lattices import (
    load_lattices_for_model_and_temperature,
    generate_and_display_lattice_animations,
)
from mcmc_tools.analysis_utils.stat_runner import analyze_and_store_latest_statistics
from mcmc_tools.analysis_utils.plots import plot_with_errorbars

RELEASE_URL = os.getenv(
    "MCMC_RELEASE_URL",
    "https://github.com/elisastph/MCMC/releases/download/v0.1.2/mcmc-linux-x86_64.tar.gz"
)


def load_config(keys=("DATABASE_URL", "SAFE_MODE")):
    # 1) Wenn ENV schon gesetzt ist, nie überschreiben
    for k in keys:
        if os.getenv(k):
            continue
        # 2) Nur versuchen, st.secrets zu lesen, wenn vorhanden
        try:
            if k in st.secrets and st.secrets[k]:
                os.environ[k] = str(st.secrets[k])
        except Exception:
            # Kein secrets.toml vorhanden – macht nichts
            pass

load_config()
load_dotenv()

SAFE = str(os.getenv("SAFE_MODE", "0")).lower() in {"1", "true", "yes"}

# Sanfte Limits in der Cloud
MAX_STEPS = 20_000 if SAFE else 100_000
MAX_L     = 32     if SAFE else 128
def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

@st.cache_resource
def ensure_mcmc_binary() -> pathlib.Path:
    exe = pathlib.Path("bin/mcmc")
    if exe.exists() and os.access(exe, os.X_OK):
        return exe

    exe.parent.mkdir(parents=True, exist_ok=True)
    tar_path = pathlib.Path("bin/mcmc.tar.gz")

    try:
        # Download
        with urllib.request.urlopen(RELEASE_URL) as r, tar_path.open("wb") as f:
            f.write(r.read())

        # Optional: Checksum
        if SHA256:
            got = _sha256(tar_path)
            if got.lower() != SHA256.lower():
                tar_path.unlink(missing_ok=True)
                raise RuntimeError(f"SHA256 mismatch: expected {SHA256}, got {got}")

        # Extract
        with tarfile.open(tar_path, "r:gz") as tf:
            tf.extractall(exe.parent)

        exe.chmod(0o755)
        tar_path.unlink(missing_ok=True)

        if not exe.exists():
            raise FileNotFoundError("mcmc not found after extraction")

        return exe

    except Exception as e:
        raise FileNotFoundError(
            f"Could not obtain mcmc binary from {RELEASE_URL}. "
            f"Set MCMC_RELEASE_* secrets or commit bin/mcmc. Error: {e}"
        )

def ensure_schema():
    eng = engine
    insp = inspect(eng)
    want = {"simulations","results","lattices","statistics"}
    have = set(insp.get_table_names())
    missing = sorted(want - have)
    if missing:
        Base.metadata.create_all(eng)
    return missing

@st.cache_resource
def _engine_cached():
    return get_engine()

engine = _engine_cached()
if os.getenv("INIT_DB", "0") in {"1","true","yes"}:
    from mcmc_tools.db.models import Base
    Base.metadata.create_all(engine)

from urllib.parse import urlparse
u = urlparse(os.environ.get("DATABASE_URL", ""))
# st.caption(f"DB → host={u.hostname}, port={u.port}, db={u.path.lstrip('/')}, user={(u.username or '')[:6]}…")

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
    mcmc_path = ensure_mcmc_binary()

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
            cmd = [str(mcmc_path), "--model", model, "--L", str(L), "--T", f"{T:.2f}", "--steps", str(steps)]
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
#     if st.sidebar.button("🛠 Build binary now"):
#         try:
#             path = ensure_mcmc_binary(src_dir="..")
#             st.success(f"Built: {path}")
#         except Exception as e:
#             st.error(f"Build failed: {e}")
