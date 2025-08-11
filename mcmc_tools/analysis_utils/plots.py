from typing import Sequence, Optional, Dict
import pandas as pd
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots
import os
from typing import List
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import streamlit as st
import plotly.graph_objects as go
from mcmc_tools.analysis_utils.io import _fetch_last_k_stats_for_model, _to_py_floats

# def plot_with_errorbars(models: List[str], L: int, steps: int, temperatures: List[float]):
#     """
#     Plottet pro Modell 4 Plotly-Charts (E, M, Cv, Chi) mit Fehlerbalken.
#     Nimmt für jedes Modell die letzten k Statistik-Einträge (k = len(temperatures)).
#     Sortiert die Punkte in den Charts nach Temperatur.
#     """
#     if not models:
#         st.warning("⚠️ No models selected.")
#         return
#     if not temperatures:
#         st.warning("⚠️ No temperatures provided.")
#         return

#     temps_py = _to_py_floats(temperatures)
#     k = len(temps_py)

#     # Debug: Inputs anzeigen
#     # st.write("🛠️ DEBUG – Requested:", {"L": L, "steps_requested": steps, "k": k, "temperatures (requested)": temps_py})

#     for model in models:
#         # letzte k Stats holen
#         df = _fetch_last_k_stats_for_model(model, L, k)

#         # Debug: was kam zurück?
#         # st.write(f"🛠️ DEBUG – fetched rows for {model}: {len(df)} (last {k} by statistics.id)")
#         # if not df.empty:
#         #     st.write({
#         #         "stat_ids(desc)": df["stat_id"].tolist(),
#         #         "temps(found, unsorted)": df["temperature"].round(2).tolist(),
#         #         "steps(found)": sorted(df["steps"].unique().tolist()),
#         #     })

#         if df.empty:
#             st.warning(f"⚠️ No statistics for {model} (L={L}) in the last {k} rows.")
#             continue

#         # Für die Plot-Achse nach Temperatur sortieren
#         df_plot = df.sort_values("temperature").reset_index(drop=True)
#         x_ticks = df_plot["temperature"].round(2).unique().tolist()

#         st.subheader(f"📈 {model} – Statistical Observables (L={L})")

#         plots = [
#             ("energy", "error_energy", r"$\langle E \rangle$/spin"),
#             ("magnetization", "error_magnetization", r"$\langle M \rangle$/spin"),
#             ("cv", "error_cv", r"Heat Capacity"),
#             ("chi", "error_chi", r"Susceptibility"),
#         ]

#         cols = st.columns(2)
#         for i, (y, yerr, label) in enumerate(plots):
#             fig = go.Figure()
#             fig.add_trace(go.Scatter(
#                 x=df_plot["temperature"],
#                 y=df_plot[y],
#                 error_y=dict(type='data', array=df_plot[yerr]),
#                 mode='lines+markers',
#                 name=label
#             ))
#             fig.update_layout(
#                 height=400,
#                 margin=dict(l=40, r=10, t=40, b=40),
#                 xaxis=dict(
#                     title="Temperature T",
#                     tickmode="array",
#                     tickvals=x_ticks
#                 ),
#                 yaxis=dict(
#                     title=label,  # Achsentitel ohne LaTeX
#                     nticks=5
#                 ),
#             )

#             with cols[i % 2]:
#                 # LaTeX-Titel über dem Plot anzeigen
#                 st.markdown(f"#### {label}", unsafe_allow_html=False)
#                 st.plotly_chart(fig, use_container_width=True)

def plot_with_errorbars(models: List[str], L: int, steps: int, temperatures: List[float]):
    if not models:
        st.warning("⚠️ No models selected.")
        return
    if not temperatures:
        st.warning("⚠️ No temperatures provided.")
        return

    temps_req = _to_py_floats(temperatures)

    for model in models:
        df = _fetch_last_k_stats_for_model(model, L, temps_req)

        if df.empty:
            st.warning(f"⚠️ No statistics for {model} (L={L}) at {temps_req}.")
            continue

        # Sanity: fehlen T-Werte?
        got = set(round(float(t), 2) for t in df["temperature_r2"].tolist())
        miss = [t for t in temps_req if t not in got]
        if miss:
            st.info(f"ℹ️ Missing temperatures for {model}: {miss} (no stats yet)")

        # Plotvorbereitung
        df_plot = df.sort_values("temperature_r2").reset_index(drop=True)
        x_ticks = df_plot["temperature_r2"].tolist()

        st.subheader(f"📈 {model} – Statistical Observables (L={L})")

        plots = [
            ("energy", "error_energy", r"$\langle E \rangle$/spin"),
            ("magnetization", "error_magnetization", r"$\langle m \rangle$/spin"),  # ggf. <|m|>
            ("cv", "error_cv", r"Heat Capacity"),
            ("chi", "error_chi", r"Susceptibility"),
        ]

        cols = st.columns(2)
        for i, (y, yerr, label) in enumerate(plots):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_plot["temperature_r2"],
                y=df_plot[y],
                error_y=dict(type='data', array=df_plot[yerr]),
                mode='lines+markers',
                name=label
            ))
            fig.update_layout(
                height=400,
                margin=dict(l=40, r=10, t=40, b=40),
                xaxis=dict(title="Temperature T", tickmode="array", tickvals=x_ticks),
                yaxis=dict(title=label, nticks=5),
            )
            with cols[i % 2]:
                st.markdown(f"#### {label}")
                st.plotly_chart(fig, use_container_width=True)

# def _line_with_error(x, y, yerr, name):
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=x, y=y, mode="lines+markers", name=name,
#         error_y=dict(type="data", array=yerr)
#     ))
#     fig.update_layout(
#         height=400,
#         margin=dict(l=40, r=10, t=40, b=40),
#         xaxis_title="Temperature T",
#         yaxis_title=name,
#     )
#     return fig

# def plot_with_errorbars(
#     models: Sequence[str],
#     L: int,
#     steps: int,
#     temperatures: Sequence[float],
#     df_stats: Optional[pd.DataFrame] = None,
#     save_dir: Optional[str] = None
# ) -> go.Figure:
#     """
#     Gibt EINE Figure mit 2x2 Subplots zurück:
#       (1,1) Energy per Spin
#       (1,2) Magnetization per Spin
#       (2,1) Heat Capacity
#       (2,2) Susceptibility
#     Erwartet df_stats mit Spalten: model, temperature, ... und error_*
#     """
#     if df_stats is None or df_stats.empty:
#         return go.Figure()

#     # filter + sort
#     temps_r2 = [round(float(t), 2) for t in temperatures]
#     df_stats = df_stats.copy()
#     if "temperature" in df_stats.columns:
#         df_stats["temperature"] = df_stats["temperature"].round(2)

#     df_plot = df_stats[
#         df_stats["model"].isin(models) & df_stats["temperature"].isin(temps_r2)
#     ]
#     if df_plot.empty:
#         return go.Figure()

#     # Subplots
#     fig = make_subplots(
#         rows=2, cols=2,
#         subplot_titles=("Energy per Spin", "Magnetization per Spin", "Heat Capacity", "Susceptibility"),
#         horizontal_spacing=0.12, vertical_spacing=0.16
#     )

#     panels = [
#         ("energy_per_spin", "error_energy",        "Energy per Spin",        1, 1),
#         ("magnetization_per_spin", "error_magnetization", "Magnetization per Spin", 1, 2),
#         ("heat_capacity", "error_cv",              "Heat Capacity",          2, 1),
#         ("susceptibility", "error_chi",            "Susceptibility",         2, 2),
#     ]

#     # traces
#     # for metric, err, y_label, row, col in panels:
#     #     for i, (model, sub) in enumerate(df_plot.groupby("model")):
#     #         sub = sub.sort_values("temperature")
#     #         fig.add_trace(
#     #             go.Scatter(
#     #                 x=sub["temperature"],
#     #                 y=sub[metric],
#     #                 mode="lines+markers",
#     #                 name=model,
#     #                 error_y=dict(type="data", array=sub[err]),
#     #                 showlegend=(row == 1 and col == 1 and i >= 0)  # Legende nur im ersten Panel
#     #             ),
#     #             row=row, col=col
#     #         )
#     #     # Achsentitel pro Panel
#     #     fig.update_xaxes(title_text="Temperature T", row=row, col=col)
#     #     fig.update_yaxes(title_text=y_label, row=row, col=col)
#     for metric, err, y_label, row, col in panels:
#         for i, (model, sub) in enumerate(df_plot.groupby("model")):
#             sub = sub.sort_values("temperature").copy()

#             # robust: cast + dropna nur für diese beiden Spalten
#             sub["temperature"] = pd.to_numeric(sub["temperature"], errors="coerce")
#             sub[metric] = pd.to_numeric(sub[metric], errors="coerce")
#             sub[err] = pd.to_numeric(sub[err], errors="coerce")
#             sub = sub.dropna(subset=["temperature", metric, err])

#             if sub.empty:
#                 continue

#             fig.add_trace(
#                 go.Scatter(
#                     x=sub["temperature"].to_numpy(),
#                     y=sub[metric].to_numpy(),
#                     mode="lines+markers",
#                     name=model,
#                     marker=dict(size=6),
#                     error_y=dict(
#                         type="data",
#                         array=sub[err].to_numpy(),
#                         visible=True,
#                         thickness=1.2,   # etwas kräftiger
#                         width=2          # Kappenbreite
#                     ),
#                     showlegend=(row == 1 and col == 1 and i >= 0)
#                 ),
#                 row=row, col=col
#             )

#     fig.update_layout(
#         height=800,
#         margin=dict(l=50, r=20, t=50, b=40),
#         legend_title_text="Model",
#     )

#     if save_dir:
#         os.makedirs(save_dir, exist_ok=True)
#         fig.write_html(os.path.join(save_dir, "combined_metrics.html"))

#     return fig
# # def plot_with_errorbars(
# #     models: Sequence[str],
# #     L: int,
# #     steps: int,
# #     temperatures: Sequence[float],
# #     df_stats: Optional[pd.DataFrame] = None,
# #     save_dir: Optional[str] = None
# # ) -> Dict[str, go.Figure]:
# #     """
# #     Entweder df_stats übergeben (Spalten: model, temperature, energy_per_spin, error_energy, ...)
# #     oder die App kümmert sich vorher ums Laden. Gibt ein Dict {metric: Figure} zurück.
# #     """
# #     if df_stats is None or df_stats.empty:
# #         return {}

# #     df_plot = df_stats[df_stats["model"].isin(models) & df_stats["temperature"].isin(temperatures)]
# #     figs: Dict[str, go.Figure] = {}

# #     for metric, err, label in [
# #         ("energy_per_spin", "error_energy", "Energy per Spin"),
# #         ("magnetization_per_spin", "error_magnetization", "Magnetization per Spin"),
# #         ("heat_capacity", "error_cv", "Heat Capacity"),
# #         ("susceptibility", "error_chi", "Susceptibility"),
# #     ]:
# #         fig = go.Figure()
# #         for model, sub in df_plot.groupby("model"):
# #             sub = sub.sort_values("temperature")
# #             fig.add_trace(go.Scatter(
# #                 x=sub["temperature"], y=sub[metric],
# #                 mode="lines+markers", name=model,
# #                 error_y=dict(type="data", array=sub[err])
# #             ))
# #         fig.update_layout(
# #             height=400,
# #             margin=dict(l=40, r=10, t=40, b=40),
# #             xaxis_title="Temperature T",
# #             yaxis_title=label,
# #             legend_title="Model",
# #         )
# #         figs[metric] = fig

# #         if save_dir:
# #             os.makedirs(save_dir, exist_ok=True)
# #             fig.write_html(os.path.join(save_dir, f"{metric}.html"))

# #     return figs

# def plot_with_errorbars_subplots(
#     models: Sequence[str],
#     L: int,
#     steps: int,
#     temperatures: Sequence[float],
#     df_stats: Optional[pd.DataFrame] = None,
#     save_dir: Optional[str] = None
# ) -> go.Figure:
#     if df_stats is None or df_stats.empty:
#         return go.Figure()

#     df_plot = df_stats[df_stats["model"].isin(models) & df_stats["temperature"].isin(temperatures)]

#     # Subplot-Layout: 2 Reihen, 2 Spalten
#     fig = make_subplots(
#         rows=2, cols=2,
#         subplot_titles=("Energy per Spin", "Magnetization per Spin", "Heat Capacity", "Susceptibility")
#     )

#     metrics = [
#         ("energy_per_spin", "error_energy", 1, 1),
#         ("magnetization_per_spin", "error_magnetization", 1, 2),
#         ("heat_capacity", "error_cv", 2, 1),
#         ("susceptibility", "error_chi", 2, 2)
#     ]

#     for metric, err, row, col in metrics:
#         for model, sub in df_plot.groupby("model"):
#             sub = sub.sort_values("temperature")
#             fig.add_trace(
#                 go.Scatter(
#                     x=sub["temperature"],
#                     y=sub[metric],
#                     mode="lines+markers",
#                     name=model if (row, col) == (1, 1) else None,  # Legende nur einmal anzeigen
#                     error_y=dict(type="data", array=sub[err])
#                 ),
#                 row=row, col=col
#             )

#     fig.update_layout(
#         height=800,
#         width=900,
#         margin=dict(l=40, r=10, t=40, b=40),
#         xaxis_title="Temperature T",
#         legend_title="Model"
#     )

#     if save_dir:
#         os.makedirs(save_dir, exist_ok=True)
#         fig.write_html(os.path.join(save_dir, "combined_metrics.html"))

#     return fig