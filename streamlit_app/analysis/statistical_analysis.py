import numpy as np
import glob
import re
from collections import defaultdict
import os
import pandas as pd
import matplotlib.pyplot as plt

def blocking_analysis(data, max_block_size=None):
    """
    Blocking method to estimate the error of correlated data.
    Returns the block sizes and corresponding variances of block means.
    """
    N = len(data)
    if max_block_size is None:
        max_block_size = N // 4

    block_sizes = []
    variances = []

    for block_size in range(1, max_block_size + 1):
        n_blocks = N // block_size
        if n_blocks < 2:
            break
        blocks = np.array([data[i * block_size:(i + 1) * block_size].mean()
                           for i in range(n_blocks)])
        block_variance = blocks.var(ddof=1)
        block_sizes.append(block_size)
        variances.append(block_variance)

    return np.array(block_sizes), np.array(variances)

def autocorrelation(data, max_lag=100):
    """
    Compute autocorrelation function of the data up to max_lag.
    """
    data = np.asarray(data)
    n = len(data)
    mean = np.mean(data)
    var = np.var(data)
    autocorr = np.correlate(data - mean, data - mean, mode='full')[n - 1:] / (var * n)
    return np.arange(max_lag), autocorr[:max_lag]

def jackknife_error(data: np.ndarray, observable_fn) -> float:
    """
    Estimate the standard error using the jackknife resampling method.

    Parameters:
    - data: 1D array of data points
    - observable_fn: function to compute the observable (e.g., np.mean)

    Returns:
    - jackknife standard error estimate
    """
    n = len(data)
    if n < 2:
        raise ValueError("Not enough data points for jackknife analysis")

    jackknife_samples = np.array([
        observable_fn(np.delete(data, i)) for i in range(n)
    ])
    jackknife_mean = np.mean(jackknife_samples)
    variance = (n - 1) / n * np.sum((jackknife_samples - jackknife_mean) ** 2)
    return np.sqrt(variance)

def jackknife_cv(energies: np.ndarray, T: float):
    n = len(energies)
    if n <= 1:
        return np.nan

    energies2 = energies ** 2
    cv_samples = []

    for i in range(n):
        e = np.delete(energies, i)
        e2 = np.delete(energies2, i)

        mean_e = np.mean(e)
        mean_e2 = np.mean(e2)
        cv = (mean_e2 - mean_e ** 2) / (T ** 2)
        cv_samples.append(cv)

    mean_cv = np.mean(cv_samples)
    variance = (n - 1) / n * np.sum((cv_samples - mean_cv) ** 2)
    return np.sqrt(variance)

def jackknife_chi(mags: np.ndarray, T: float):
    n = len(mags)
    if n <= 1:
        return np.nan

    mags2 = mags ** 2
    chi_samples = []

    for i in range(n):
        m = np.delete(mags, i)
        m2 = np.delete(mags2, i)

        mean_m = np.mean(m)
        mean_m2 = np.mean(m2)
        chi = (mean_m2 - mean_m ** 2) / T
        chi_samples.append(chi)

    mean_chi = np.mean(chi_samples)
    variance = (n - 1) / n * np.sum((chi_samples - mean_chi) ** 2)
    return np.sqrt(variance)


if __name__ == "__main__":

    input_dir = "streamlit_app/results"
    output_dir = "streamlit_app/analysis_results"

    output_dir_1 = os.path.join(output_dir, "visualize_with_error")
    output_dir_2 = os.path.join(output_dir, "autocorrelation_blocking")
    output_csv_dir = os.path.join(output_dir, "csv")
    
    os.makedirs(output_dir_1, exist_ok=True)
    os.makedirs(output_dir_2, exist_ok=True)
    os.makedirs(output_csv_dir, exist_ok=True)

    # 1. Load data und sort after model & temperature
    files = sorted(glob.glob(os.path.join(input_dir, "results_*.csv")))
    results_by_model = defaultdict(list)
    data_by_model = defaultdict(list) 

    for file in files:
        match = re.search(r"results_([A-Za-z]+)_L(\d+)_T([0-9]+(?:\.[0-9]+)?)\.csv", os.path.basename(file))
        if not match:
            print(f"Skipped file: {file}")
            continue

        model = match.group(1)
        L = int(match.group(2))
        T = float(match.group(3))
        norm = L * L

        df = pd.read_csv(file)
        if df.empty:
            continue

        equil_df = df[df["step"] >= df["step"].max() * 0.5]
        if equil_df.empty:
            continue

        # KEINE doppelte Normierung!
        mean_E = equil_df["energy"].mean()
        mean_E2 = equil_df["energy_squared"].mean()
        mean_M = equil_df["magnetization"].mean()
        mean_M2 = equil_df["magnetization_squared"].mean()

        # Dann erst normieren:
        mean_E /= norm
        mean_E2 /= norm**2
        mean_M /= norm
        mean_M2 /= norm**2

        # Fluktuationen
        C_v = (mean_E2 - mean_E ** 2) / (T ** 2)
        chi = (mean_M2 - mean_M ** 2) / T

        # Statistische Analyse vorbereiten
        data_by_model[model].append({
            "T": T,
            "energy_data": equil_df["energy"].values / norm,
            "magnetization_data": equil_df["magnetization"].values / norm,
            "c_v_data": C_v,
            "chi_data": chi
        })

    for model, entries in data_by_model.items():
        for entry in entries:
            T = entry["T"]
            energy = entry["energy_data"]
            mag = entry["magnetization_data"]
            C_v = entry["c_v_data"]
            chi = entry["chi_data"]

            # Blocking
            block_sizes, block_vars = blocking_analysis(energy)
            plt.plot(block_sizes, block_vars)
            plt.xlabel("Block size")
            plt.ylabel("Var(block means)")
            plt.title(f"Blocking Analysis - {model} - T={T:.2f}")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{output_dir_2}/blocking_{model}_T{T:.2f}.png")
            plt.close()

            # Autokorrelation
            lags, acf = autocorrelation(energy)
            plt.plot(lags[:len(acf)], acf)

            plt.xlabel("Lag")
            plt.ylabel("Autocorrelation")
            plt.title(f"Autocorrelation - {model} - T={T:.2f}")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{output_dir_2}/acf_{model}_T{T:.2f}.png")
            plt.close()

            # Jackknife
            err_E = jackknife_error(energy, np.mean)
            err_M = jackknife_error(mag, np.mean)
            err_Cv = jackknife_cv(energy, T)
            err_Chi = jackknife_chi(mag, T)

            results_by_model[model].append({
                "Temperature": T,
                "Energy_per_spin": np.mean(energy),
                "Magnetization_per_spin": np.mean(mag),
                "Cv": C_v,
                "Susceptibility": chi,
                "Error_Energy": err_E,
                "Error_Magnetization": err_M,
                "Error_Cv": err_Cv,
                "Error_Chi": err_Chi
            })
            
            print(f"[{model} | T={T:.2f}] ⟨E⟩/spin = {np.mean(energy):.4f} ± {err_E:.4f}")
            print(f"[{model} | T={T:.2f}] ⟨M⟩/spin = {np.mean(mag):.4f} ± {err_M:.4f}")
            print(f"[{model} | T={T:.2f}] Cv = {C_v:.6f} ± {err_Cv:.6f}")
            print(f"[{model} | T={T:.2f}] chi = {chi:.6f} ± {err_Chi:.6f}")

        df = pd.DataFrame(results_by_model[model]).sort_values("Temperature")
        csv_path = os.path.join(output_csv_dir, f"{model.lower()}_results.csv")
        df.to_csv(csv_path, index=False)

    for model, data in results_by_model.items():
        df = pd.DataFrame(data).sort_values("Temperature")

        # Plot 1: Energy per spin
        plt.figure(figsize=(6, 4))
        plt.errorbar(df["Temperature"], df["Energy_per_spin"], yerr=df["Error_Energy"],
                    fmt="o-", capsize=3, color="tab:blue", label="⟨E⟩/spin")
        plt.xlabel("Temperature T")
        plt.ylabel("Energy per spin")
        plt.title(f"{model} Model: Energy vs Temperature")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        filename = os.path.join(output_dir_1, f"{model.lower()}_Energy_per_spin_vs_Temperature.png")
        plt.savefig(filename)
        plt.close()
        print(f"✅ Plot gespeichert: {filename}")

        # Plot 2: Magnetization per spin
        plt.figure(figsize=(6, 4))
        plt.errorbar(df["Temperature"], df["Magnetization_per_spin"], yerr=df["Error_Magnetization"],
                    fmt="o-", capsize=3, color="tab:red", label="⟨M⟩/spin")
        plt.xlabel("Temperature T")
        plt.ylabel("Magnetization per spin")
        plt.title(f"{model} Model: Magnetization vs Temperature")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        # filename = f"{output_dir}/{model.lower()}_Magnetization_per_spin_vs_Temperature.png"
        filename = os.path.join(output_dir_1, f"{model.lower()}_Magnetization_per_spin_vs_Temperature.png")
        plt.savefig(filename)
        plt.close()
        print(f"✅ Plot gespeichert: {filename}")

        # Plot 3: Heat Capacity Cv
        plt.figure(figsize=(6, 4))
        plt.errorbar(df["Temperature"], df["Cv"], yerr=df["Error_Cv"],
                    fmt="o-", capsize=3, color="tab:green", label="$C_v$")
        plt.xlabel("Temperature T")
        plt.ylabel("Heat Capacity $C_v$")
        plt.title(f"{model} Model: Heat Capacity vs Temperature")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        # filename = f"{output_dir}/{model.lower()}_Cv_vs_Temperature.png"
        filename = os.path.join(output_dir_1, f"{model.lower()}_Cv_vs_Temperature.png")
        plt.savefig(filename)
        plt.close()
        print(f"✅ Plot gespeichert: {filename}")

        # Plot 4: Susceptibility χ
        plt.figure(figsize=(6, 4))
        plt.errorbar(df["Temperature"], df["Susceptibility"], yerr=df["Error_Chi"],
                    fmt="o-", capsize=3, color="tab:purple", label="$\\chi$")
        plt.xlabel("Temperature T")
        plt.ylabel("Susceptibility $\\chi$")
        plt.title(f"{model} Model: Susceptibility vs Temperature")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        # filename = f"{output_dir}/{model.lower()}_Susceptibility_vs_Temperature.png"
        filename = os.path.join(output_dir_1, f"{model.lower()}_Susceptibility_vs_Temperature.png")
        plt.savefig(filename)
        plt.close()
        print(f"✅ Plot gespeichert: {filename}")
