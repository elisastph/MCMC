import argparse
from mcmc_tools.analysis_utils.io import load_results, save_df

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["Ising","Clock","XY"])
    p.add_argument("--T", type=float)
    p.add_argument("--out", default="analysis_results/results.csv")
    args = p.parse_args()

    df = load_results(args.model, args.T)
    save_df(df, args.out)
    print(f"✅ Saved raw results: {args.out} ({len(df)} rows)")
