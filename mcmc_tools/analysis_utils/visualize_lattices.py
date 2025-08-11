from __future__ import annotations
from typing import Tuple, List, Sequence
import os
import base64
import io

import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio  # GIF Export

from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Lattice, Simulation

from typing import Tuple, List
import base64, io, numpy as np
from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Simulation, Lattice

import numpy as np
import plotly.graph_objects as go
import plotly.figure_factory as ff
import streamlit as st


from typing import Optional, Tuple, List
import base64, io, warnings
import numpy as np
from mcmc_tools.db.connection import get_session
from mcmc_tools.db.models import Simulation, Lattice

def _decode_b64_to_array(b64: str) -> np.ndarray:
    raw = base64.b64decode(b64.encode("utf-8"))
    buf = io.BytesIO(raw)
    return np.load(buf, allow_pickle=False)

def load_lattices_for_model_and_temperature(
    model: str,
    T: float,
    L: Optional[int] = None,  # <- optionaler L-Filter
) -> Tuple[List[int], List[np.ndarray]]:
    """
    Lädt (steps, lattices) für die neueste Simulation zu (model, T[, L]).
    Wenn L angegeben ist, wird exakt diese Gittergröße gewählt.
    Frames mit abweichender Form werden verworfen.
    """
    with get_session() as s:
        q = s.query(Simulation.id).filter(
            Simulation.model == model,
            Simulation.temperature == float(T),
        )
        if L is not None:
            q = q.filter(Simulation.lattice_size == int(L))

        # Neueste passende Simulation
        sim_id = q.order_by(Simulation.created_at.desc(), Simulation.id.desc()) \
                  .limit(1).scalar()
        if sim_id is None:
            return [], []

        rows = (
            s.query(Lattice.step, Lattice.data)
             .filter(Lattice.simulation_id == sim_id)
             .order_by(Lattice.step.asc())
             .all()
        )

    if not rows:
        return [], []

    # Decodieren
    steps_all, lats_all = [], []
    for stp, b64 in rows:
        arr = _decode_b64_to_array(b64)
        steps_all.append(int(stp))
        lats_all.append(arr)

    # Falls L explizit gegeben ist: strikter Shape‑Guard
    if L is not None:
        keep_steps, keep_lats, dropped = [], [], []
        for stp, lat in zip(steps_all, lats_all):
            if isinstance(lat, np.ndarray) and lat.ndim == 2 and lat.shape == (L, L):
                keep_steps.append(stp)
                keep_lats.append(lat)
            else:
                dropped.append((stp, getattr(lat, "shape", None)))
        if dropped:
            warnings.warn(f"Dropped {len(dropped)} frames with wrong shape for L={L}: {dropped[:5]}{'...' if len(dropped)>5 else ''}")
        # dedupe steps (falls doppelt)
        seen = set()
        out_steps, out_lats = [], []
        for stp, lat in zip(keep_steps, keep_lats):
            if stp in seen: 
                continue
            seen.add(stp)
            out_steps.append(stp)
            out_lats.append(lat)
        return out_steps, out_lats

    # Ohne L: Mehrheitsshape wählen (robust, falls alte/versch. L gemischt)
    shapes = [lat.shape for lat in lats_all]
    from collections import Counter
    majority_shape, _ = max(Counter(shapes).items(), key=lambda kv: kv[1])

    keep_steps, keep_lats, dropped = [], [], []
    for stp, lat in zip(steps_all, lats_all):
        if lat.shape == majority_shape:
            keep_steps.append(stp)
            keep_lats.append(lat)
        else:
            dropped.append((stp, lat.shape))
    if dropped:
        warnings.warn(f"Dropped {len(dropped)} frames with non-majority shapes: {dropped[:5]}{'...' if len(dropped)>5 else ''}")

    # dedupe steps
    seen = set()
    out_steps, out_lats = [], []
    for stp, lat in zip(keep_steps, keep_lats):
        if stp in seen:
            continue
        seen.add(stp)
        out_steps.append(stp)
        out_lats.append(lat)

    return out_steps, out_lats
# def load_lattices_for_model_and_temperature(model: str, T: float) -> Tuple[List[int], List[np.ndarray]]:
#     """Lädt (steps, lattices) für GENAU EINE (neueste) Simulation zu (model, T)."""
#     with get_session() as s:
#         # 1) Neueste Simulation für (model, T) bestimmen
#         sim_id = (
#             s.query(Simulation.id)
#              .filter(Simulation.model == model, Simulation.temperature == float(T))
#              .order_by(Simulation.created_at.desc(), Simulation.id.desc())
#              .limit(1)
#              .scalar()
#         )
#         if sim_id is None:
#             return [], []

#         # 2) Nur Lattices dieser Simulation laden
#         rows = (
#             s.query(Lattice.step, Lattice.data)
#              .filter(Lattice.simulation_id == sim_id)
#              .order_by(Lattice.step.asc())
#              .all()
#         )

#     if not rows:
#         return [], []

#     # 3) Doppelte Steps vorsichtig rausfiltern
#     seen = set()
#     steps, lattices = [], []
#     for stp, b64 in rows:
#         if stp in seen:
#             continue
#         seen.add(stp)
#         steps.append(int(stp))
#         lattices.append(_decode_b64_to_array(b64))
#     return steps, lattices

def _auto_stride(H: int, target_arrows_per_axis: int = 24) -> int:
    # Ein Pfeil pro Zelle bei kleinen Gittern, sonst so, dass ~target Pfeile pro Achse rauskommen
    if H <= target_arrows_per_axis:
        return 1
    return max(1, H // target_arrows_per_axis)

def _quiver_traces_from_lattice_centered(U_ds: np.ndarray, V_ds: np.ndarray,
                                         stride: int, orig_shape: tuple[int,int],
                                         line_width: float = 2.0):
    """
    Build quiver traces with the arrow CENTERED on the true cell center in the ORIGINAL grid.
    U_ds, V_ds are downsampled fields of shape (H_ds, W_ds).
    """
    H, W = orig_shape
    Hd, Wd = U_ds.shape

    # centers in original coords
    jj, ii = np.meshgrid(np.arange(Wd), np.arange(Hd))
    Xc = jj * stride + stride * 0.5
    Yc = ii * stride + stride * 0.5

    # arrow length scaled to cell size
    scale = 0.9 * stride  # volle Länge innerhalb der Zelle

    # Normiere (U,V), um nur Richtung zu behalten
    mag = np.sqrt(U_ds**2 + V_ds**2)
    mag[mag == 0] = 1.0  # Division vermeiden
    U_dir = U_ds / mag
    V_dir = V_ds / mag

    # Tail so setzen, dass Mittelpunkt auf (Xc, Yc) liegt
    Xt = Xc - 0.5 * scale * U_dir
    Yt = Yc - 0.5 * scale * V_dir
    U_plot = scale * U_dir
    V_plot = scale * V_dir

    fig_q = ff.create_quiver(
        Xt.flatten(), Yt.flatten(),
        U_plot.flatten(), V_plot.flatten(),
        scale=1.0, arrow_scale=0.35, name="quiver",
        line=dict(width=line_width)
    )
    return list(fig_q.data), (H, W)

def animate_ising(steps, lattices, T: float, stride: int = 1):
    if not lattices: return None
    H, W = lattices[0].shape

    def downsample(arr): return arr[::stride, ::stride] if stride > 1 else arr

    L0 = downsample(lattices[0])
    U0 = np.zeros_like(L0)
    V0 = L0
    base_traces, (Hfix, Wfix) = _quiver_traces_from_lattice_centered(U0, V0, stride, (H, W))

    frames = []
    for i, lat in enumerate(lattices):
        Ld = downsample(lat)
        U = np.zeros_like(Ld)
        V = Ld
        frame_traces, _ = _quiver_traces_from_lattice_centered(U, V, stride, (H, W))
        frames.append(go.Frame(name=str(steps[i]), data=frame_traces))

    fig = go.Figure(data=base_traces, frames=frames)
    fig.update_xaxes(visible=False, range=[0, Wfix], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[Hfix, 0])  # reversed
    fig.update_layout(
        title=f"Ising – T={T:.2f}", height=520, margin=dict(l=20, r=20, t=50, b=20),
        updatemenus=[{
            "buttons": [
                {"args": [None, {"frame": {"duration": 120, "redraw": True},
                                 "fromcurrent": True, "mode": "immediate"}],
                 "label": "▶ Play", "method": "animate"},
                {"args": [[None], {"frame": {"duration": 0, "redraw": True},
                                   "mode": "immediate"}],
                 "label": "⏸ Pause", "method": "animate"}
            ],
            "direction": "left", "pad": {"r": 10, "t": 10},
            "type": "buttons", "x": 0.0, "xanchor": "left", "y": 1.05, "yanchor": "top",
            "showactive": False
        }],
        sliders=[{
            "active": 0, "currentvalue": {"prefix": "Step: "},
            "steps": [{"args": [[str(s)], {"frame": {"duration": 0, "redraw": True},
                                          "mode": "immediate"}],
                       "label": str(s), "method": "animate"} for s in steps]
        }]
    )
    return fig

def animate_clock(steps, lattices, T: float, M: int = 8, stride: int = 2):
    if not lattices: return None
    H, W = lattices[0].shape

    def downsample(arr): return arr[::stride, ::stride] if stride > 1 else arr
    def to_uv(lat):
        Ld = downsample(lat)
        theta = 2 * np.pi * (Ld % M) / float(M)
        return np.cos(theta), np.sin(theta)

    U0, V0 = to_uv(lattices[0])
    base_traces, (Hfix, Wfix) = _quiver_traces_from_lattice_centered(U0, V0, stride, (H, W))

    frames = []
    for i, lat in enumerate(lattices):
        U, V = to_uv(lat)
        frame_traces, _ = _quiver_traces_from_lattice_centered(U, V, stride, (H, W))
        frames.append(go.Frame(name=str(steps[i]), data=frame_traces))

    fig = go.Figure(data=base_traces, frames=frames)
    fig.update_xaxes(visible=False, range=[0, Wfix], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[Hfix, 0])
    fig.update_layout(
        title=f"Clock (M={M}) – T={T:.2f}", height=520, margin=dict(l=20, r=20, t=50, b=20),
        updatemenus=[{
            "buttons": [
                {"args": [None, {"frame": {"duration": 120, "redraw": True},
                                 "fromcurrent": True, "mode": "immediate"}],
                 "label": "▶ Play", "method": "animate"},
                {"args": [[None], {"frame": {"duration": 0, "redraw": True},
                                   "mode": "immediate"}],
                 "label": "⏸ Pause", "method": "animate"}
            ],
            "direction": "left", "pad": {"r": 10, "t": 10},
            "type": "buttons", "x": 0.0, "xanchor": "left", "y": 1.05, "yanchor": "top",
            "showactive": False
        }],
        sliders=[{
            "active": 0, "currentvalue": {"prefix": "Step: "},
            "steps": [{"args": [[str(s)], {"frame": {"duration": 0, "redraw": True},
                                          "mode": "immediate"}],
                       "label": str(s), "method": "animate"} for s in steps]
        }]
    )
    return fig

def animate_xy(steps, lattices, T: float, stride: int = 2):
    if not lattices: return None
    H, W = lattices[0].shape

    def downsample(arr): return arr[::stride, ::stride] if stride > 1 else arr
    def to_uv(lat):
        Ld = downsample(lat)
        theta = np.mod(Ld, 2*np.pi)
        return np.cos(theta), np.sin(theta)

    U0, V0 = to_uv(lattices[0])
    base_traces, (Hfix, Wfix) = _quiver_traces_from_lattice_centered(U0, V0, stride, (H, W))

    frames = []
    for i, lat in enumerate(lattices):
        U, V = to_uv(lat)
        frame_traces, _ = _quiver_traces_from_lattice_centered(U, V, stride, (H, W))
        frames.append(go.Frame(name=str(steps[i]), data=frame_traces))

    fig = go.Figure(data=base_traces, frames=frames)
    fig.update_xaxes(visible=False, range=[0, Wfix], scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, range=[Hfix, 0])
    fig.update_layout(
        title=f"XY – T={T:.2f}", height=520, margin=dict(l=20, r=20, t=50, b=20),
        updatemenus=[{
            "buttons": [
                {"args": [None, {"frame": {"duration": 120, "redraw": True},
                                 "fromcurrent": True, "mode": "immediate"}],
                 "label": "▶ Play", "method": "animate"},
                {"args": [[None], {"frame": {"duration": 0, "redraw": True},
                                   "mode": "immediate"}],
                 "label": "⏸ Pause", "method": "animate"}
            ],
            "direction": "left", "pad": {"r": 10, "t": 10},
            "type": "buttons", "x": 0.0, "xanchor": "left", "y": 1.05, "yanchor": "top",
            "showactive": False
        }],
        sliders=[{
            "active": 0, "currentvalue": {"prefix": "Step: "},
            "steps": [{"args": [[str(s)], {"frame": {"duration": 0, "redraw": True},
                                          "mode": "immediate"}],
                       "label": str(s), "method": "animate"} for s in steps]
        }]
    )
    return fig


# ------------------------------------------------------------
# Integrator
# ------------------------------------------------------------
def generate_and_display_lattice_animations(models, T_target: float, output_dir: str, display_width: int = 500, M_clock: int = 8, stride: int = 2):
    """
    Ersetzt GIF-Workflow. Lädt Lattices, baut Plotly-Quiver-Animationen, rendert direkt.
    """
    # from .visualize_lattices import load_lattices_for_model_and_temperature  # dein Loader bleibt gleich

    if not models:
        st.warning("Please select at least one model for analysis.")
        return

    cols = st.columns(len(models))
    for col, model in zip(cols, models):
        with col:
            steps, lattices = load_lattices_for_model_and_temperature(model, T_target)
            if not steps:
                st.warning(f"No lattices found for {model} at T={T_target:.2f}")
                continue

            H, W = lattices[0].shape
            s = _auto_stride(H, target_arrows_per_axis=24)  # bei 16×16 ⇒ s=1

            model_l = model.lower()
            if model_l == "ising":
                fig = animate_ising(steps, lattices, T_target, stride=s)
            elif model_l == "clock":
                fig = animate_clock(steps, lattices, T_target, M=M_clock, stride=s)
            elif model_l == "xy":
                fig = animate_xy(steps, lattices, T_target, stride=s)
            else:
                st.warning(f"Unknown model: {model}")
                continue

            if fig is None:
                st.warning(f"Could not build animation for {model}.")
                continue
            st.plotly_chart(fig, use_container_width=True)
