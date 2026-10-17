"""
S2-07: Shared-author network.

Idea: two DAOs are connected if the same wallet created proposals in both.
Edge weight = number of distinct authors the two DAOs have in common.
(This is the prototype of notebooks/02_data_quality.ipynb turned into a script.)

Two things matter for correctness:
1. Authors are lowercased. Snapshot stores many addresses in mixed case
   (checksum) and the other platforms in lowercase, so without this the same
   wallet would count as two different authors.
2. Tally and Realms proposals have NO author, so they can never create an edge.
   A missing author is NOT evidence of "no relationship".

Output (data/processed/): edges_authors.csv, authors_coverage_by_platform.csv
Run from the project root:  python src/shared_authors.py
"""

import random
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_author_proposals():
    """Return one row per (author, DAO) and the table of nodes."""
    proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_clean.csv", low_memory=False)
    deployments = pd.read_csv(PROCESSED_DATA_DIR / "deployments_clean.csv", low_memory=False)

    # Nodes = catalogue + DAOs that have proposals but are not in the catalogue
    # (the 6 Snapshot spaces of S2-02), so no proposal is left without a node.
    nodes = deployments[["deployment_id", "platform"]]
    missing = (
        proposals.loc[~proposals["dao_id"].isin(nodes["deployment_id"]), ["dao_id", "platform"]]
        .drop_duplicates()
        .rename(columns={"dao_id": "deployment_id"})
    )
    nodes = pd.concat([nodes, missing], ignore_index=True)

    # Normalization: lowercase the wallet address
    proposals["author"] = proposals["author"].str.lower()

    pairs = (
        proposals.dropna(subset=["author"])[["author", "dao_id"]]
        .drop_duplicates()  # an author counts once per DAO
        .rename(columns={"dao_id": "deployment_id"})
    )
    return proposals, pairs, nodes


def generate_author_edges(pairs):
    """For each author, every pair of DAOs they proposed in adds 1 to that pair."""
    counter = Counter()
    for _, daos in pairs.groupby("author")["deployment_id"]:
        for dao_a, dao_b in combinations(sorted(daos.unique()), 2):
            counter[(dao_a, dao_b)] += 1

    return pd.DataFrame(
        [(a, b, n) for (a, b), n in counter.items()],
        columns=["source", "target", "shared_authors"],
    )


def validate_edges(edges, pairs, nodes):
    """Check endpoints are nodes, and recompute some pairs with plain sets."""
    node_ids = set(nodes["deployment_id"])
    assert edges["source"].isin(node_ids).all() and edges["target"].isin(node_ids).all(), \
        "Some edge endpoints are not in the node table"

    authors_of = pairs.groupby("deployment_id")["author"].apply(set)
    random.seed(42)
    chosen = list(edges.nlargest(5, "shared_authors").index) + random.sample(list(edges.index), 5)

    rows = []
    for i in chosen:
        edge = edges.loc[i]
        by_hand = len(authors_of[edge["source"]] & authors_of[edge["target"]])
        rows.append((edge["source"], edge["target"], edge["shared_authors"], by_hand,
                     by_hand == edge["shared_authors"]))
    report = pd.DataFrame(rows, columns=["source", "target", "table", "sets", "match"])
    print(report.to_string(index=False))
    assert report["match"].all(), "Some pairs do not match their hand calculation"


def coverage_by_platform(proposals, nodes, edges):
    """Which share of proposals / DAOs can take part in the author network."""
    in_edges = set(edges["source"]) | set(edges["target"])

    table = pd.DataFrame({
        "proposals": proposals.groupby("platform").size(),
        "with_author": proposals.dropna(subset=["author"]).groupby("platform").size(),
        "daos": nodes.groupby("platform").size(),
        "daos_with_author_proposal": proposals.dropna(subset=["author"])
        .groupby("platform")["dao_id"].nunique(),
        "daos_in_author_edges": nodes[nodes["deployment_id"].isin(in_edges)]
        .groupby("platform").size(),
    }).fillna(0).astype(int)
    table["pct_proposals_with_author"] = (100 * table["with_author"] / table["proposals"]).round(1)
    table["pct_daos_in_edges"] = (100 * table["daos_in_author_edges"] / table["daos"]).round(1)
    return table


if __name__ == "__main__":
    proposals, pairs, nodes = load_author_proposals()
    print(f"Authors: {pairs['author'].nunique()} | DAOs with authors: {pairs['deployment_id'].nunique()}")

    edges = generate_author_edges(pairs)
    print(f"Edges: {len(edges)} | total weight: {edges['shared_authors'].sum()}")

    print("\nValidation (table vs recomputation with sets):")
    validate_edges(edges, pairs, nodes)

    coverage = coverage_by_platform(proposals, nodes, edges)
    print("\nCoverage by platform:")
    print(coverage.to_string())

    # Edges by pair of platforms
    platform_of = nodes.set_index("deployment_id")["platform"]
    pair_platforms = (
        pd.DataFrame({"a": edges["source"].map(platform_of), "b": edges["target"].map(platform_of)})
        .apply(lambda r: " - ".join(sorted([r["a"], r["b"]])), axis=1)
    )
    print("\nEdges by platform pair:")
    print(pair_platforms.value_counts().to_string())

    edges.to_csv(PROCESSED_DATA_DIR / "edges_authors.csv", index=False)
    coverage.to_csv(PROCESSED_DATA_DIR / "authors_coverage_by_platform.csv")
