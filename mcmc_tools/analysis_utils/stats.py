import numpy as np
import pandas as pd

def _block_indices(n, block_size):
    """Erzeuge Liste von (start, end)-Indices für Blöcke der Länge block_size."""
    blocks = []
    i = 0
    while i < n:
        j = min(n, i + block_size)
        blocks.append((i, j))
        i = j
    return blocks

def _block_jackknife_errors_for_sim(sub: pd.DataFrame, L: int, T: float, use_abs_magnetization: bool=True):
    """
    Schätzt Std-Fehler für e_bar, m_bar, c_v, chi innerhalb EINER Simulation
    via Leave-One-Block-Out Jackknife über die Zeitreihe (Steps).
    """
    sub = sub.sort_values("step")[["energy", "magnetization", "energy_squared", "magnetization_squared"]].to_numpy()
    n = sub.shape[0]
    if n <= 1:
        return (float("nan"),)*4

    N = float(L * L)
    E = sub[:,0]; M = sub[:,1]; E2 = sub[:,2]; M2 = sub[:,3]
    AbsM = np.abs(M)

    block_size = max(1, n // 20)
    blocks = _block_indices(n, block_size)
    if len(blocks) <= 1:
        e_err  = float(np.std(E / N, ddof=1) / np.sqrt(max(1, n)))
        m_src  = AbsM / N if use_abs_magnetization else M / N
        m_err  = float(np.std(m_src, ddof=1) / np.sqrt(max(1, n)))
        cv_s   = (E2 - E**2) / (N * (T**2))
        chi_s  = (M2 - M**2) / (N * T)  # immer M, nicht AbsM!
        cv_err = float(np.std(cv_s, ddof=1) / np.sqrt(max(1, n)))
        chi_err= float(np.std(chi_s, ddof=1) / np.sqrt(max(1, n)))
        return e_err, m_err, cv_err, chi_err

    S_E, S_M, S_E2, S_M2, S_AbsM = E.sum(), M.sum(), E2.sum(), M2.sum(), AbsM.sum()

    jk_e, jk_m, jk_cv, jk_chi = [], [], [], []
    for a, b in blocks:
        n_k = n - (b - a)
        if n_k <= 0:
            continue

        sE   = S_E   - E[a:b].sum()
        sM   = S_M   - M[a:b].sum()
        sE2  = S_E2  - E2[a:b].sum()
        sM2  = S_M2  - M2[a:b].sum()
        sAbs = S_AbsM - AbsM[a:b].sum()

        E_mean  = sE / n_k
        M_mean  = sM / n_k
        E2_mean = sE2 / n_k
        M2_mean = sM2 / n_k
        AbsM_mean = sAbs / n_k

        e_bar = E_mean / N
        m_bar = (AbsM_mean / N) if use_abs_magnetization else (M_mean / N)
        cv    = (E2_mean - E_mean**2) / (N * (T**2))
        chi   = (M2_mean - M_mean**2) / (N * T)  # immer M

        jk_e.append(e_bar)
        jk_m.append(m_bar)
        jk_cv.append(cv)
        jk_chi.append(chi)

    def jk_std(vals):
        vals = np.asarray(vals, dtype=float)
        g = len(vals)
        if g <= 1:
            return float("nan")
        m = vals.mean()
        return float(np.sqrt((g - 1) / g * np.sum((vals - m) ** 2)))

    return jk_std(jk_e), jk_std(jk_m), jk_std(jk_cv), jk_std(jk_chi)


def compute_statistics(df: pd.DataFrame, use_abs_magnetization: bool = True) -> pd.DataFrame:
    """
    Gibt jetzt **pro simulation_id** eine Zeile mit Kennzahlen **und Fehlern** zurück.
    Fehler werden innerhalb der Simulation über Steps (Block-Jackknife) geschätzt.
    """
    if df.empty:
        return df

    needed = {"simulation_id","model","temperature","lattice_size","step",
              "energy","magnetization","energy_squared","magnetization_squared"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"compute_statistics: missing columns: {sorted(missing)}")

    out_rows = []
    for (sim_id, model, T, L), sub in df.groupby(["simulation_id","model","temperature","lattice_size"]):
        sub = sub.sort_values("step")
        N = float(L*L)

        E_mean  = sub["energy"].mean()
        M_mean  = sub["magnetization"].mean()
        E2_mean = sub["energy_squared"].mean()
        M2_mean = sub["magnetization_squared"].mean()
        AbsM_mean = np.abs(sub["magnetization"]).mean()

        e_bar = E_mean / N
        m_bar = (AbsM_mean / N) if use_abs_magnetization else (M_mean / N)
        cv    = (E2_mean - E_mean**2) / (N * (T**2))
        chi   = (M2_mean - M_mean**2) / (N * T)  # immer M

        e_err, m_err, cv_err, chi_err = _block_jackknife_errors_for_sim(
            sub, L=int(L), T=float(T), use_abs_magnetization=use_abs_magnetization
        )

        out_rows.append(dict(
            simulation_id=int(sim_id),
            model=model,
            temperature=float(T),
            lattice_size=int(L),
            energy_per_spin=float(e_bar),
            magnetization_per_spin=float(m_bar),
            heat_capacity=float(cv),
            susceptibility=float(chi),
            error_energy=float(e_err),
            error_magnetization=float(m_err),
            error_cv=float(cv_err),
            error_chi=float(chi_err),
        ))

    return pd.DataFrame(out_rows).sort_values(["model","temperature","simulation_id"]).reset_index(drop=True)
