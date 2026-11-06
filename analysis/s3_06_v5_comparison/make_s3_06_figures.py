"""
S3-06: figures that compare the Sprint 2 results (Zenodo v4) with the rerun on v5.

  fig1  group weight and non-group wallets excluded, by threshold
  fig2  share of wallets by number of DAOs
  fig3  rank by weighted degree of the 15 hubs selected in Sprint 2 (graph max100)

Only reads CSV files. Usage (from the working folder of S3-06):
  python <repo>/analysis/s3_06_v5_comparison/make_s3_06_figures.py --v4 <repo>/results --v5 results --out figures
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

C4, C5 = "#4C78A8", "#F58518"      # v4, v5
THRESHOLDS = ["no limit", "300", "200", "150", "100", "75", "50"]


def read(root, area, name):
    return pd.read_csv(Path(root) / area / name)


def fig_threshold(v4, v5, out):
    t4 = read(v4, "S2-03", "S2-03_threshold_comparison.csv").astype({"threshold": str}).set_index("threshold")
    t5 = read(v5, "S2-03", "S2-03_threshold_comparison.csv").astype({"threshold": str}).set_index("threshold")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    ax = axes[0]
    x = range(len(THRESHOLDS))
    ax.bar([i - 0.2 for i in x], t4.loc[THRESHOLDS, "pct_group_weight"], 0.4, color=C4, label="v4")
    ax.bar([i + 0.2 for i in x], t5.loc[THRESHOLDS, "pct_group_weight"], 0.4, color=C5, label="v5")
    for i, th in enumerate(THRESHOLDS):
        ax.text(i - 0.2, t4.loc[th, "pct_group_weight"] + 0.8, f"{t4.loc[th, 'pct_group_weight']:.1f}", ha="center", fontsize=8)
        ax.text(i + 0.2, t5.loc[th, "pct_group_weight"] + 0.8, f"{t5.loc[th, 'pct_group_weight']:.1f}", ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(THRESHOLDS)
    ax.set_xlabel("Threshold (maximum DAOs per wallet)")
    ax.set_ylabel("% of the graph weight that comes from the group")
    ax.set_title("The group weighs less in v5, and almost nothing at 100")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    ths = ["100", "75", "50", "40"]
    x = range(len(ths))
    ax.bar([i - 0.2 for i in x], t4.loc[ths, "excluded_others"], 0.4, color=C4, label="v4")
    ax.bar([i + 0.2 for i in x], t5.loc[ths, "excluded_others"], 0.4, color=C5, label="v5")
    for i, th in enumerate(ths):
        ax.text(i - 0.2, t4.loc[th, "excluded_others"] + 8, str(int(t4.loc[th, "excluded_others"])), ha="center", fontsize=8)
        ax.text(i + 0.2, t5.loc[th, "excluded_others"] + 8, str(int(t5.loc[th, "excluded_others"])), ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(ths)
    ax.set_xlabel("Threshold (maximum DAOs per wallet)")
    ax.set_ylabel("Excluded wallets that are NOT in the group")
    ax.set_title("At 100: 0 in v4, 2 in v5")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(out / "S3-06_fig1_threshold.png", dpi=150)
    plt.close(fig)


def fig_activity(v4, v5, out):
    a4 = read(v4, "S2-03", "S2-03_activity_distribution.csv").set_index("dao_band")
    a5 = read(v5, "S2-03", "S2-03_activity_distribution.csv").set_index("dao_band")
    bands = [b for b in a5.index if b in a4.index]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    y = range(len(bands))
    ax.barh([i + 0.2 for i in y], a4.loc[bands, "percent"], 0.4, color=C4, label="v4")
    ax.barh([i - 0.2 for i in y], a5.loc[bands, "percent"], 0.4, color=C5, label="v5")
    for i, b in enumerate(bands):
        ax.text(max(a4.loc[b, "percent"], 1e-4) * 1.15, i + 0.2, f"{a4.loc[b, 'percent']:.3g}%", va="center", fontsize=8)
        ax.text(max(a5.loc[b, "percent"], 1e-4) * 1.15, i - 0.2, f"{a5.loc[b, 'percent']:.3g}%", va="center", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(1e-4, 600)
    ax.set_yticks(list(y))
    ax.set_yticklabels(bands)
    ax.invert_yaxis()
    ax.set_xlabel("% of wallets (log scale)")
    ax.set_ylabel("DAOs in which the wallet votes")
    ax.set_title("More one-DAO voters in v5; the heavy tail is the same")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "S3-06_fig2_activity.png", dpi=150)
    plt.close(fig)


def fig_hubs(v4, v5, out):
    s4 = read(v4, "S2-09", "S2-09_selected_hubs.csv").set_index("name")
    s5 = read(v5, "S2-09", "S2-09_selected_hubs.csv").set_index("name")
    nf = read(v5, "S2-09", "S2-09_selected_hubs_not_found.csv").set_index("name")
    col = "rank_weighted_max100"
    rows = []
    for name in s4.index:
        r4 = s4.loc[name, col]
        if name in s5.index:
            rows.append((name, r4, s5.loc[name, col], True))
        else:
            rows.append((name, r4, nf.loc[name, col], False))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(8.5, 5.6))
    for i, (name, a, b, found) in enumerate(rows):
        ax.plot([a, b], [i, i], color="#BBBBBB", lw=1.5, zorder=1)
        ax.scatter(a, i, color=C4, s=45, zorder=2, label="v4" if i == 0 else None)
        ax.scatter(b, i, color=C5, s=45, zorder=2, label="v5" if i == 0 else None,
                   facecolors=C5 if found else "white", edgecolors=C5, linewidths=1.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r[0]}{'' if r[3] else '  *'}" for r in rows])
    ax.invert_yaxis()
    ax.set_xscale("log")
    ax.set_xlabel("Rank by weighted degree in the max100 graph (1 = highest, log scale)")
    ax.set_title("Hubs selected in Sprint 2: they move down because new hubs enter above")
    ax.legend(frameon=False, loc="upper right")
    ax.text(0.01, 0.02, "* no longer among the 60 candidates in v5 (hollow marker)", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=8, color="#555555")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "S3-06_fig3_hub_ranks.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v4", type=Path, required=True, help="results folder of Sprint 2 (v4)")
    parser.add_argument("--v5", type=Path, required=True, help="results folder of the rerun on v5")
    parser.add_argument("--out", type=Path, default=Path("figures"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    fig_threshold(args.v4, args.v5, args.out)
    fig_activity(args.v4, args.v5, args.out)
    fig_hubs(args.v4, args.v5, args.out)
    print(f"Figures written to {args.out}")


if __name__ == "__main__":
    main()
