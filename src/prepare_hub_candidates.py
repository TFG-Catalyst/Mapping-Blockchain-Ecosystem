"""
S2-09 (part independent of S2-05/06): table of hub candidates.

Takes the S2-04 graphs and prepares, for the nodes that stand out the most
in the working configuration (max100), a sheet with:
  - node data (deployments.csv): name, platform, proposals, unique voters, website;
  - degree and weighted degree in the 4 S2-04 configurations and their rank
    in each one (persistence);
  - the 5 main neighbors with their weight in max100;
  - verified identity (results/S2-09/S2-09_verified_identity.csv), if there is one.

It does NOT compute Jaccard or any normalized measure (that is S2-05/06,
Rodrigo's): the column is left for when there are results.

Usage (from the repository root):
  python scripts/prepare_hub_candidates.py
Options: --top N (candidates per criterion, default 25), --reference
(default max100). It only reads; it writes to results/S2-09/:
  S2-09_hub_candidates.csv, S2-09_main_neighbors.csv
"""

import argparse
from pathlib import Path

import pandas as pd

CONFIGS = ["nolimit", "max200", "max100", "max50"]


def parse_arguments():
    parser = argparse.ArgumentParser(description="Hub candidates (S2-09).")
    parser.add_argument("--s204", type=Path, default=Path("results/S2-04"))
    parser.add_argument("--s209", type=Path, default=Path("results/S2-09"))
    parser.add_argument("--deployments", type=Path, default=Path("data/raw/deployments.csv"))
    parser.add_argument("--reference", default="max100")
    parser.add_argument("--top", type=int, default=25)
    return parser.parse_args()


def main():
    args = parse_arguments()
    ref = args.reference

    # Data of each DAO (lowercase ids)
    deployments = pd.read_csv(args.deployments)
    deployments["deployment_id"] = deployments["deployment_id"].astype("string").str.lower()
    deployments = deployments.drop_duplicates("deployment_id").set_index("deployment_id")

    # Degree and weighted degree of each node in each configuration (from S2-04)
    nodes = pd.read_csv(args.s204 / "S2-04_nodes_by_config.csv").set_index("deployment_id")

    # Rank of each node in each configuration (1 = the largest), by the two criteria.
    rank_columns = {}
    for criterion, prefix in [("degree", "degree_"), ("weighted", "weighted_degree_")]:
        for config in CONFIGS:
            column = nodes[f"{prefix}{config}"]
            rank_columns[f"rank_{criterion}_{config}"] = column.rank(ascending=False, method="first").astype(int)
    ranks = pd.DataFrame(rank_columns)

    # Candidates: union of the top-N by degree and by weighted degree in the reference.
    top_by_degree = set(ranks.index[ranks[f"rank_degree_{ref}"] <= args.top])
    top_by_weighted = set(ranks.index[ranks[f"rank_weighted_{ref}"] <= args.top])
    candidates = top_by_degree | top_by_weighted

    # Table of candidates: S2-04 data + ranks + data from deployments.csv
    dao_columns = ["platform", "proposals_count", "unique_voters", "votes_count", "website"]
    table = nodes.loc[sorted(candidates)]
    table = table.join(ranks)
    table = table.join(deployments[dao_columns], rsuffix="_dep")
    if "platform_dep" in table.columns:
        table["platform"] = table["platform"].fillna(table["platform_dep"])

    # Best and worst rank of each node among the 4 configurations
    rank_degree_cols = []
    rank_weighted_cols = []
    for config in CONFIGS:
        rank_degree_cols.append(f"rank_degree_{config}")
        rank_weighted_cols.append(f"rank_weighted_{config}")
    table["rank_degree_best"] = table[rank_degree_cols].min(axis=1)
    table["rank_degree_worst"] = table[rank_degree_cols].max(axis=1)
    table["rank_weighted_best"] = table[rank_weighted_cols].min(axis=1)
    table["rank_weighted_worst"] = table[rank_weighted_cols].max(axis=1)

    # Main neighbors in the reference configuration.
    # An edge appears twice: once seen from each end ("hub" is the candidate).
    edges = pd.read_csv(args.s204 / f"edges_{ref}.csv")
    with_candidate = edges[edges["source"].isin(candidates) | edges["target"].isin(candidates)]
    source_is_hub = with_candidate[with_candidate["source"].isin(candidates)]
    source_is_hub = source_is_hub.rename(columns={"source": "hub", "target": "neighbor"})
    target_is_hub = with_candidate[with_candidate["target"].isin(candidates)]
    target_is_hub = target_is_hub.rename(columns={"target": "hub", "source": "neighbor"})
    long = pd.concat([source_is_hub, target_is_hub])

    # For each hub: its 5 neighbors with the most shared voters
    long = long.sort_values(["hub", "shared_voters"], ascending=[True, False])
    long = long.groupby("hub").head(5).copy()
    long["position"] = long.groupby("hub").cumcount() + 1
    long["hub_name"] = long["hub"].map(deployments["name"])
    long["neighbor_name"] = long["neighbor"].map(deployments["name"])
    long["neighbor_unique_voters"] = long["neighbor"].map(deployments["unique_voters"])
    neighbor_columns = ["hub", "hub_name", "position", "neighbor", "neighbor_name",
                        "shared_voters", "neighbor_unique_voters"]
    long[neighbor_columns].to_csv(args.s209 / "S2-09_main_neighbors.csv", index=False)

    # One text per hub: "Name1 (weight1); Name2 (weight2); ..."
    neighbors_text = {}
    for hub, group in long.groupby("hub"):
        parts = []
        for name, weight in zip(group["neighbor_name"].astype(str), group["shared_voters"]):
            parts.append(f"{name} ({weight:,})")
        neighbors_text[hub] = "; ".join(parts)
    table["main_neighbors"] = pd.Series(neighbors_text).reindex(table.index)

    # Verified identity (if it exists) and column pending from Rodrigo.
    identity = pd.read_csv(args.s209 / "S2-09_verified_identity.csv").set_index("deployment_id")
    table["verified_identity"] = identity["verified_label"].reindex(table.index).fillna("pending")
    table["normalized_measure_S2_05_06"] = ""  # pending from Rodrigo

    # Order of the columns of the output file
    column_order = ["name", "platform", "proposals_count", "unique_voters", "votes_count",
                    "website", "verified_identity"]
    for config in CONFIGS:
        column_order.append(f"degree_{config}")
    for config in CONFIGS:
        column_order.append(f"weighted_degree_{config}")
    column_order = column_order + rank_degree_cols + rank_weighted_cols
    column_order = column_order + ["rank_degree_best", "rank_degree_worst",
                                   "rank_weighted_best", "rank_weighted_worst",
                                   "main_neighbors", "normalized_measure_S2_05_06"]
    table = table[column_order].sort_values(f"rank_weighted_{ref}")
    table.to_csv(args.s209 / "S2-09_hub_candidates.csv")

    # Short view on screen
    print(f"{len(table)} candidates (union of top {args.top} by degree and by weighted degree in {ref}).")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 22)
    view_columns = ["name", "platform", f"rank_degree_{ref}", f"rank_weighted_{ref}",
                    "rank_weighted_best", "rank_weighted_worst", "verified_identity"]
    view = table[view_columns].copy()
    view["verified_identity"] = view["verified_identity"].str[:14]
    print(view.to_string())


if __name__ == "__main__":
    main()
