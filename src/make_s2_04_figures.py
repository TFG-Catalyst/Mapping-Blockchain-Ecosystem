"""
S2-04: figures for the documentation.

Generates 3 PNG figures from the CSVs in results/S2-04 (it recomputes nothing
from votes.csv):

  S2-04_fig1_edges.png            edges and edges with weight >= 2 per configuration
  S2-04_fig2_group_weight.png     total weight per configuration, separating the weight
                                  contributed by the group of 469 wallets
  S2-04_fig3_hub_stability.png    hubs of the top 100 that stay in all 4
                                  configurations, by degree and by weighted degree

Internal check: the weight per activity band (S2-04_stability_bands.csv),
accumulated, must match the total weight of each configuration
(S2-04_metrics_by_config.csv). If it does not match, the script stops.

Usage (from the repository root):
  python scripts/make_s2_04_figures.py

It only reads CSVs; the only thing it writes are the 3 PNGs in results/S2-04/.
Requires pandas and matplotlib.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # draw to files, without opening a window
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

FOLDER = Path("results/S2-04")

# Colors
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRAY = "#898781"
LIGHT_GRAY = "#c3c2b7"
GRID = "#e1e0d9"
BLUE = "#2a78d6"      # series 1
ORANGE = "#eb6834"    # series 2
BAR_GRAY = "#b9b8b0"

# Configurations in the order they are drawn, and their names on the charts
ORDER = ["nolimit", "max200", "max100", "max50"]
LABELS = {
    "nolimit": "No limit",
    "max200": "Max. 200",
    "max100": "Max. 100",
    "max50": "Max. 50",
}

# General style of all the charts
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": LIGHT_GRAY,
    "axes.labelcolor": INK_2,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "text.color": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def thousands(x):
    """Integer with thousands separator: 1234567 -> '1,234,567'."""
    return f"{int(round(x)):,}"


def format_tick(value, position):
    """Text shown on each axis tick (matplotlib calls this function)."""
    return thousands(value)


def percent_text(x, decimals=1):
    return f"{x:.{decimals}f}%"


def config_labels():
    """Text under each bar. The working configuration gets an extra line."""
    labels = []
    for config in ORDER:
        text = LABELS[config]
        if config == "max100":
            text = text + "\n(working configuration)"
        labels.append(text)
    return labels


def clean(ax):
    """Removes the left line and adds a light horizontal grid."""
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def load():
    metrics = pd.read_csv(FOLDER / "S2-04_metrics_by_config.csv").set_index("config")
    bands = pd.read_csv(FOLDER / "S2-04_stability_bands.csv")
    hubs = pd.read_csv(FOLDER / "S2-04_stability_hubs.csv")

    missing = []
    for config in ORDER:
        if config not in metrics.index:
            missing.append(config)
    if len(missing) > 0:
        sys.exit(f"ERROR: configurations missing in the metrics: {missing}")
    return metrics.loc[ORDER], bands, hubs


# ----------------------------------------------------------------------
# Figure 1: edges per configuration
# ----------------------------------------------------------------------
def fig1(metrics):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), constrained_layout=True)
    panels = [
        ("edges", "Edges"),
        ("edges_weight_ge_2", "Edges with weight ≥ 2"),
    ]

    for panel_number in range(2):
        ax = axes[panel_number]
        column, title = panels[panel_number]
        values = metrics[column].tolist()

        # The working configuration is drawn in blue, the others in gray
        colors = []
        for config in ORDER:
            if config == "max100":
                colors.append(BLUE)
            else:
                colors.append(BAR_GRAY)

        x_positions = list(range(len(ORDER)))
        ax.bar(x_positions, values, width=0.55, color=colors, edgecolor=SURFACE, linewidth=1.5)
        for x, value in zip(x_positions, values):
            ax.text(x, value + max(values) * 0.015, thousands(value),
                    ha="center", va="bottom", fontsize=9, color=INK)

        ax.set_xticks(x_positions)
        ax.set_xticklabels(config_labels(), fontsize=9)
        ax.set_ylim(0, max(values) * 1.12)
        ax.yaxis.set_major_formatter(FuncFormatter(format_tick))
        ax.set_title(title, loc="left", fontsize=11, color=INK)
        clean(ax)

    removed = metrics.loc["max200", "edges"] - metrics.loc["max100", "edges"]
    removed_pct = percent_text(100 * removed / metrics.loc["max200", "edges"])
    fig.suptitle(f"Going from max. 200 to max. 100 removes {thousands(removed)} edges ({removed_pct})",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, -0.06,
             "The four graphs are nested (max. 50 ⊂ max. 100 ⊂ max. 200 ⊂ no limit). "
             "After applying the S2-02 exclusions.",
             fontsize=8.5, color=INK_2, ha="left")
    return fig


# ----------------------------------------------------------------------
# Figure 2: weight contributed by the group
# ----------------------------------------------------------------------
def weights_by_config(metrics, bands):
    """Total weight and group weight accumulated per configuration, from the bands."""
    bands = bands.set_index("wallet_dao_band")
    band_order = ["2-50", "51-100", "101-200", ">200"]
    if list(bands.index) != band_order:
        sys.exit(f"ERROR: the expected bands are {band_order} and there are {list(bands.index)}")

    # How many bands each configuration includes
    bands_included = {"max50": 1, "max100": 2, "max200": 3, "nolimit": 4}

    total_weight = {}
    group_weight = {}
    for config, how_many in bands_included.items():
        selected = band_order[:how_many]
        total_weight[config] = int(bands.loc[selected, "weight"].sum())
        group_weight[config] = int(bands.loc[selected, "group_weight"].sum())

        expected = int(metrics.loc[config, "total_weight"])
        if total_weight[config] != expected:
            sys.exit(f"ERROR: the accumulated weight of the bands ({total_weight[config]}) "
                     f"does not match that of {config} ({expected})")
    return total_weight, group_weight


def fig2(metrics, bands):
    total_weight, group_weight = weights_by_config(metrics, bands)

    # Weight of the rest of the wallets and weights in millions (to draw)
    rest_millions = []
    group_millions = []
    for config in ORDER:
        rest_millions.append((total_weight[config] - group_weight[config]) / 1e6)
        group_millions.append(group_weight[config] / 1e6)

    fig, ax = plt.subplots(figsize=(8.6, 5), constrained_layout=True)
    x_positions = list(range(len(ORDER)))
    ax.bar(x_positions, rest_millions, width=0.5, color=BLUE,
           edgecolor=SURFACE, linewidth=2, label="Rest of wallets")
    ax.bar(x_positions, group_millions, width=0.5, bottom=rest_millions, color=ORANGE,
           edgecolor=SURFACE, linewidth=2, label="Group of 469 wallets")

    # Texts above each bar: total weight and % that comes from the group
    for x, config in zip(x_positions, ORDER):
        top = total_weight[config] / 1e6
        share = group_weight[config] / total_weight[config]
        if share < 0.01:
            decimals = 2
        else:
            decimals = 1
        ax.text(x, top + 0.12, thousands(total_weight[config]),
                ha="center", va="bottom", fontsize=9, color=INK)
        ax.text(x, top + 0.55, f"group: {percent_text(100 * share, decimals)}",
                ha="center", va="bottom", fontsize=9, color=ORANGE, fontweight="bold")

    ax.set_xticks(x_positions)
    ax.set_xticklabels(config_labels(), fontsize=9)
    ax.set_ylabel("Total edge weight (millions)")
    ax.set_ylim(0, max(total_weight.values()) / 1e6 * 1.18)
    clean(ax)
    ax.legend(frameon=False, loc="upper right", fontsize=9, bbox_to_anchor=(1.0, 0.86))
    ax.set_title("The threshold decides how much the group weighs: "
                 "from half of the weight with no limit to 1.9% with max. 100",
                 loc="left", fontsize=12, fontweight="bold")
    return fig


# ----------------------------------------------------------------------
# Figure 3: stability of the hubs
# ----------------------------------------------------------------------
def fig3(hubs):
    # One row per criterion: how many nodes are stable, how many change and
    # the median % of group weight of the ones that change
    rows = []
    for criterion, label in [("degree", "By degree"), ("weighted_degree", "By weighted degree")]:
        nodes = hubs[hubs["criterion"] == criterion]
        stable_nodes = nodes[nodes["stable_top100"] == True]
        changing_nodes = nodes[nodes["stable_top100"] == False]
        rows.append({
            "label": label,
            "stable": len(stable_nodes),
            "varying": len(changing_nodes),
            "median_group_pct": changing_nodes["pct_group_weight"].median(),
        })

    fig, ax = plt.subplots(figsize=(9, 3.1), constrained_layout=True)

    # The first row goes at the top, so the y positions are reversed
    y_positions = [1, 0]
    for y, row in zip(y_positions, rows):
        stable = row["stable"]
        varying = row["varying"]
        ax.barh(y, stable, height=0.36, color=BLUE, edgecolor=SURFACE, linewidth=2)
        ax.barh(y, varying, left=stable, height=0.36, color=ORANGE, edgecolor=SURFACE, linewidth=2)
        ax.text(stable / 2, y, f"{stable} stable",
                ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        if varying >= 20:
            # Wide enough bar: the text goes inside it
            ax.text(stable + varying / 2, y, f"{varying} change",
                    ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        else:
            # Narrow bar: the text goes to its right
            ax.text(stable + varying + 2, y, f"{varying} change",
                    ha="left", va="center", color=ORANGE, fontsize=9.5, fontweight="bold")

    row_labels = []
    longest_bar = 0
    for row in rows:
        row_labels.append(row["label"])
        if row["stable"] + row["varying"] > longest_bar:
            longest_bar = row["stable"] + row["varying"]

    ax.set_yticks(y_positions)
    ax.set_yticklabels(row_labels, fontsize=10)
    ax.set_xlabel("Nodes that are in the top 100 of at least one of the 4 configurations")
    ax.tick_params(axis="both", length=0)
    ax.spines["left"].set_visible(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(0, longest_bar * 1.12)
    ax.set_title("Hubs by degree are stable; those with the highest weighted degree change with the configuration",
                 loc="left", fontsize=12, fontweight="bold")

    # Footnote: median % of group weight, for the weighted degree
    median_changing = rows[1]["median_group_pct"]
    weighted = hubs[hubs["criterion"] == "weighted_degree"]
    stable_weighted = weighted[weighted["stable_top100"] == True]
    median_stable = stable_weighted["pct_group_weight"].median()
    fig.text(0.01, -0.04,
             f"Stable = in the top 100 in all 4 configurations. For weighted degree, those that change receive a median of "
             f"{percent_text(median_changing, 0)} of their weight from the group; the stable ones, {percent_text(median_stable, 0)}.",
             fontsize=8.5, color=INK_2, ha="left")
    return fig


def main():
    metrics, bands, hubs = load()
    figures = [
        ("S2-04_fig1_edges.png", fig1(metrics)),
        ("S2-04_fig2_group_weight.png", fig2(metrics, bands)),
        ("S2-04_fig3_hub_stability.png", fig3(hubs)),
    ]
    for name, fig in figures:
        path = FOLDER / name
        fig.savefig(path, dpi=160, facecolor=SURFACE, bbox_inches="tight")
        plt.close(fig)
        print("written", path)


if __name__ == "__main__":
    main()
