import argparse, os
import pandas as pd
from mcmc_tools.analysis_utils.plots import plot_with_errorbars

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stats", default="analysis_results/statistics.csv")
    p.add_argument("--outdir", default="analysis_results/plots")
    p.add_argument("--models", nargs="*", default=["Ising","Clock","XY"])
    args = p.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = pd.read_csv(args.stats)
    figs = plot_with_errorbars(args.models, L=0, steps=0, temperatures=df["temperature"].unique(), df_stats=df, save_dir=args.outdir)
    print(f"✅ Plots saved to: {args.outdir} ({len(figs)} figures)")
