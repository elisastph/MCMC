import pandas as pd
import matplotlib.pyplot as plt
import glob
import re
from collections import defaultdict
import os

# Alle CSV-Dateien sammeln
files = sorted(glob.glob("../results/results_*.csv"))
results_by_model = defaultdict(list)

output_dir = "../analysis_results/visualize_no_error"
os.makedirs(output_dir, exist_ok=True)

for file in files:
    match = re.search(r"results_([A-Za-z]+)_L(\d+)_T([0-9]+(?:\.[0-9]+)?)\.csv", os.path.basename(file))
    if not match:
        print(f"⚠️ Datei übersprungen: {file}")
        continue

    model = match.group(1)
    L = int(match.group(2))
    T = float(match.group(3))

    df = pd.read_csv(file)
    if df.empty:
        continue

    equil_df = df[df["step"] >= df["step"].max() * 0.5]
    if equil_df.empty:
        continue

    # Normierung pro Spin
    norm = L * L
    mean_E = equil_df["energy"].mean() / norm
    mean_M = equil_df["magnetization"].mean() / norm
    mean_E2 = equil_df["energy_squared"].mean() / (norm ** 2)
    mean_M2 = equil_df["magnetization_squared"].mean() / (norm ** 2)

    C_v = (mean_E2 - mean_E ** 2) / (T ** 2)
    chi = (mean_M2 - mean_M ** 2) / T

    results_by_model[model].append({
        "Temperature": T,
        "Energy_per_spin": mean_E,
        "Magnetization_per_spin": mean_M,
        "Cv": C_v,
        "Susceptibility": chi
    })
# Plot für jedes Modell separat
for model, data in results_by_model.items():
    df = pd.DataFrame(data).sort_values("Temperature")

    # plt.figure(figsize=(8, 6))
    # plt.plot(df["Temperature"], df["Energy_per_spin"], label="⟨E⟩/spin")
    # plt.plot(df["Temperature"], df["Magnetization_per_spin"], label="⟨M⟩/spin")
    # plt.xlabel("Temperature T")
    # plt.ylabel("Observable")
    # plt.title(f"{model} Model: Temperature Dependence")
    # plt.grid(True)
    # plt.legend()
    # plt.tight_layout()
    # plt.savefig(f"{model.lower()}.png")
    # print(f"✅ Plot gespeichert: {model.lower()}.png")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    # Energie-Plot
    ax1.plot(df["Temperature"], df["Energy_per_spin"], label="⟨E⟩/spin", color="tab:blue")
    ax1.set_ylabel("Energy per spin")
    ax1.set_title(f"{model} Model: Temperature Dependence")
    ax1.grid(True)
    ax1.legend()

    # Magnetisierung-Plot
    ax2.plot(df["Temperature"], df["Magnetization_per_spin"], label="⟨M⟩/spin", color="tab:red")
    ax2.set_xlabel("Temperature T")
    ax2.set_ylabel("Magnetization per spin")
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    # plt.savefig(f"../analysis_results/{model.lower()}.png")
    plt.savefig(os.path.join(output_dir, f"{model.lower()}_energy_magnetization.png"))
    print(f"Plot gespeichert: {model.lower()}.png")

    # Neues Figure für Cv und χ
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    ax3.plot(df["Temperature"], df["Cv"], label="Heat Capacity $C_v$", color="tab:green")
    ax3.set_ylabel("Heat Capacity $C_v$")
    ax3.set_title(f"{model} Model: Fluctuations")
    ax3.grid(True)
    ax3.legend()

    ax4.plot(df["Temperature"], df["Susceptibility"], label="Susceptibility $\\chi$", color="tab:purple")
    ax4.set_xlabel("Temperature T")
    ax4.set_ylabel("Susceptibility $\\chi$")
    ax4.grid(True)
    ax4.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{model.lower()}_fluctuations.png"))
    print(f"Plot gespeichert: {model.lower()}_fluctuations.png")
