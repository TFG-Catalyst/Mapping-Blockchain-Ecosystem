"""
S2-06: How does normalization (Jaccard) change which relationships stand out?

Input : data/processed/edges_jaccard.csv (S2-05) and deployments_clean.csv (names)
Output: docs/figures/S2-06_*.png and data/processed/s2_06_*.csv
Run from the project root:  python src/normalization_comparison.py

Reading guide
- shared_voters (count) grows with community SIZE.
- jaccard measures PROPORTIONAL overlap (share of voters in common).
We compare the two on the same reference graph (max_daos = 100).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"

# Edges with fewer shared voters are ignored: with 1-9 voters Jaccard is unstable
MIN_SHARED_VOTERS = 10
TOP_PERCENTILE = 0.95  # "high" = top 5% of the edges

# Colours: first three slots of the validated palette + neutral grey
BLUE, ORANGE, AQUA, GREY = "#287ce4", "#e95c24", "#1dd192", "#b5b4ae"


def load_edges():
    edges = pd.read_csv(DATA_DIR / "edges_jaccard.csv")
    edges = edges[edges["shared_voters"] >= MIN_SHARED_VOTERS].copy()

    names = pd.read_csv(DATA_DIR / "deployments_clean.csv", usecols=["deployment_id", "name"])
    names = names.set_index("deployment_id")["name"].to_dict()
    #Hard-coded name for the Optimism DAO, which is not in the deployments_clean.csv file. 
    names["eip155:10:0xcdf27f107725988f2261ce2256bdfcde8b382b10"] = "Optimism Governance (named 'test')"
    label = lambda dao: names.get(dao) if isinstance(names.get(dao), str) else dao
    edges["pair"] = edges["source"].map(label) + "  -  " + edges["target"].map(label)
    return edges, label


def classify_edges(edges):
    """Four types of edge according to count (size) and Jaccard (overlap)."""
    high_count = edges["shared_voters"] >= edges["shared_voters"].quantile(TOP_PERCENTILE)
    high_jaccard = edges["jaccard"] >= edges["jaccard"].quantile(TOP_PERCENTILE)

    edges["type"] = "neither"
    edges.loc[high_count & ~high_jaccard, "type"] = "size effect"        # big communities
    edges.loc[~high_count & high_jaccard, "type"] = "proportional overlap"  # small, near-identical
    edges.loc[high_count & high_jaccard, "type"] = "both"
    return edges


def top_k_overlap(edges, ks=(10, 50, 100, 500, 1000)):
    """How many of the 'K' strongest edges by count are also top 'K' by Jaccard (K -> top 10, 50, 100, 500, 1000 edges)"""
    rows = []
    for k in ks:
        by_count = set(edges.nlargest(k, "shared_voters").index)
        by_jaccard = set(edges.nlargest(k, "jaccard").index)
        rows.append((k, len(by_count & by_jaccard), 100 * len(by_count & by_jaccard) / k))
    return pd.DataFrame(rows, columns=["K", "common", "pct_common"])


def deployment_ranks(edges, label):
    """Rank every deployment by strength = sum of its edge weights, under each measure."""
    def strength(column):
        return pd.concat([edges.groupby("source")[column].sum(),
                          edges.groupby("target")[column].sum()], axis=1).fillna(0).sum(axis=1)

    ranks = pd.DataFrame({"strength_count": strength("shared_voters"),
                          "strength_jaccard": strength("jaccard")})
    ranks["rank_count"] = ranks["strength_count"].rank(ascending=False, method="first").astype(int)
    ranks["rank_jaccard"] = ranks["strength_jaccard"].rank(ascending=False, method="first").astype(int)
    ranks["name"] = [label(dao) for dao in ranks.index]
    return ranks.sort_values("rank_count")


# figures
def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)


def figure_scatter(edges):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    colours = {"neither": GREY, "size effect": ORANGE, "proportional overlap": AQUA, "both": BLUE}
    for kind, colour in colours.items():  # grey first, so the coloured ones stay on top
        part = edges[edges["type"] == kind]
        ax.scatter(part["shared_voters"], part["jaccard"], s=5 if kind == "neither" else 9,
                   color=colour, alpha=0.35 if kind == "neither" else 0.8, linewidths=0,
                   label=f"{kind} ({len(part):,})")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("shared voters (count)"); ax.set_ylabel("Jaccard")
    ax.set_title(f"Same edges, two rankings (edges with at least {MIN_SHARED_VOTERS} shared voters)",
                 loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="lower right", markerscale=2)
    style(ax)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "S2-06_scatter_count_vs_jaccard.png", dpi=160)


def figure_overlap(overlap):
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.bar(overlap["K"].astype(str), overlap["pct_common"], color=BLUE, width=0.55)
    for i, value in enumerate(overlap["pct_common"]):
        ax.text(i, value + 0.6, f"{value:.0f}%", ha="center", fontsize=9)
    ax.set_xlabel("K strongest edges"); ax.set_ylabel("% in both top-K lists")
    ax.set_title("Top edges by count vs by Jaccard barely coincide", loc="left", fontsize=11)
    style(ax)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "S2-06_top_k_overlap.png", dpi=160)


def figure_rank_change(ranks, n=8):
    """Dumbbell: the top deployments by count vs by Jaccard, with their rank in the other measure."""
    chosen = pd.concat([ranks.nsmallest(n, "rank_count"), ranks.nsmallest(n, "rank_jaccard")])
    chosen = chosen.drop_duplicates().sort_values("rank_count", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for y, (_, row) in enumerate(chosen.iterrows()):
        ax.plot([row["rank_count"], row["rank_jaccard"]], [y, y], color=GREY, linewidth=1)
    ax.scatter(chosen["rank_count"], range(len(chosen)), color=ORANGE, s=40, label="rank by count", zorder=3)
    ax.scatter(chosen["rank_jaccard"], range(len(chosen)), color=AQUA, s=40, label="rank by Jaccard", zorder=3)
    ax.set_yticks(range(len(chosen))); ax.set_yticklabels(chosen["name"].str[:28], fontsize=8)
    ax.set_xscale("log"); ax.set_xlabel("rank (1 = most prominent, log scale)")
    ax.set_title("Prominent deployments change completely with the measure", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8, loc="upper center")
    style(ax)
    fig.tight_layout(); fig.savefig(FIGURES_DIR / "S2-06_rank_change_deployments.png", dpi=160)


if __name__ == "__main__":
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    edges, label = load_edges()
    edges = classify_edges(edges)
    print(f"Edges analysed (>= {MIN_SHARED_VOTERS} shared voters): {len(edges):,}")
    print(edges["type"].value_counts().to_string())

    overlap = top_k_overlap(edges)
    print("\nTop-K edges in common:\n", overlap.round(1).to_string(index=False))

    ranks = deployment_ranks(edges, label)
    for k in (10, 50):
        common = set(ranks.nsmallest(k, "rank_count").index) & set(ranks.nsmallest(k, "rank_jaccard").index)
        print(f"Top {k} deployments in common (count vs Jaccard): {len(common)}")

    # Examples to read: 5 strongest edges of each type
    examples = (edges.sort_values("shared_voters", ascending=False)
                .groupby("type").head(5)[["type", "pair", "shared_voters", "jaccard"]])
    print("\n", examples.round(4).to_string(index=False))

    examples.to_csv(DATA_DIR / "s2_06_examples.csv", index=False)
    ranks.to_csv(DATA_DIR / "s2_06_deployment_ranks.csv")
    figure_scatter(edges); figure_overlap(overlap); figure_rank_change(ranks)
