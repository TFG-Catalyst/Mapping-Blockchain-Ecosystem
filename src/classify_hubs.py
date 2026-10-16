"""
S2-09: objective indicators to classify hubs.

For each candidate node it computes (on the S2-04 graphs, reference max100):
  - persistence: rank by weighted degree in the 4 configurations and the
    difference between the best and the worst;
  - group weight: % of its weighted degree in the nolimit graph that comes
    from the 469 wallets of the S2-03 group (taken from
    S2-04_stability_hubs.csv);
  - size: unique voters (deployments.csv) and its rank among all nodes;
  - main neighbor: its weight and the proportion with respect to the unique
    voters of both (indicative: unique_voters may have a different coverage
    than the votes of the graph, see S2-05; the exact proportion is
    computed by S2-05/06);
  - same organization: whether among its 5 main neighbors there is a node of
    its same organization (manual assignment below, only where there is
    evidence).

Candidates = those in S2-09_hub_candidates.csv + the nodes that are in the
top N by weighted degree of any configuration.

Flags (thresholds in the constants):
  F_filter   group weight >= GROUP_THRESHOLD
  F_overlap  main neighbor with proportion >= OVERLAP_THRESHOLD and rank by
             degree much worse than by weighted degree (few neighbors,
             huge weights)
  F_size     among the TOP_SIZE nodes with the most unique voters
  F_org      a main neighbor belongs to its same organization

Usage (from the repository root): python scripts/classify_hubs.py [--top N]
Writes results/S2-09/S2-09_hub_indicators.csv. It only reads.
"""

import argparse
from pathlib import Path

import pandas as pd

CONFIGS = ["nolimit", "max200", "max100", "max50"]
GROUP_THRESHOLD = 30.0     # % of the weight (nolimit) that comes from the group
OVERLAP_THRESHOLD = 0.80   # weight of the main neighbor / unique voters of the smaller of the two
DEGREE_GAP = 100           # rank difference between rank by degree and by weighted degree
TOP_SIZE = 30              # ranks by unique voters

# Manual assignment of organization (evidence: verified identity in
# S2-09_verified_identity.csv; Snapshot spaces without a row in that file are
# assigned by their name and remain to be checked on snapshot.org).
ORGANIZATION = {
    "eip155:42161:0x789fc99093b09ad01c34dc7251d0c89ce743e5a4": "Arbitrum",
    "eip155:42161:0xf07ded9dc292157749b6fd268e37df6ea38395b9": "Arbitrum",
    "arbitrumfoundation.eth": "Arbitrum",
    "uniswapgovernance.eth": "Uniswap",
    "eip155:1:0x408ed6354d4973f66138c91495f2f2fcbd8724c3": "Uniswap",
    "aavedao.eth": "Aave",
    "eip155:1:0xec568fffba86c094cf06b22134b23074dfe2252c": "Aave",
    "eip155:324:0x76705327e682f2d96943280d99464ab61219e34f": "zkSync",
    "eip155:324:0x10560f8b7ee37571ad7e3702eeb12bc422036e89": "zkSync",
}


def parse_arguments():
    parser = argparse.ArgumentParser(description="Indicators to classify hubs (S2-09).")
    # 60: the results of S2-09 were generated with --top 60 (78 nodes)
    parser.add_argument("--top", type=int, default=60)
    parser.add_argument("--s204", type=Path, default=Path("results/S2-04"))
    parser.add_argument("--s209", type=Path, default=Path("results/S2-09"))
    parser.add_argument("--deployments", type=Path, default=Path("data/raw/deployments.csv"))
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Data of each DAO (lowercase ids)
    deployments = pd.read_csv(args.deployments)
    deployments["deployment_id"] = deployments["deployment_id"].astype("string").str.lower()
    deployments = deployments.drop_duplicates("deployment_id").set_index("deployment_id")

    # Degree and weighted degree of each node in each configuration (from S2-04)
    nodes = pd.read_csv(args.s204 / "S2-04_nodes_by_config.csv").set_index("deployment_id")

    # Rank by weighted degree in each configuration (1 = the largest)
    weighted_ranks = {}
    for config in CONFIGS:
        column = nodes[f"weighted_degree_{config}"]
        weighted_ranks[config] = column.rank(ascending=False, method="first").astype(int)
    weighted_ranks = pd.DataFrame(weighted_ranks)

    # Rank by degree in max100 and rank by unique voters
    degree_rank = nodes["degree_max100"].rank(ascending=False, method="first").astype(int)
    unique_voters = deployments["unique_voters"]
    unique_voters_rank = unique_voters.rank(ascending=False, method="first")

    # Candidates: those of the candidates file + the top N of any configuration
    candidates = set(pd.read_csv(args.s209 / "S2-09_hub_candidates.csv")["deployment_id"])
    for config in CONFIGS:
        in_top = weighted_ranks[config] <= args.top
        candidates = candidates | set(weighted_ranks.index[in_top])
    candidates = sorted(candidates)

    # % of the weight of each node (nolimit) that comes from the group
    group_table = pd.read_csv(args.s204 / "S2-04_stability_hubs.csv")
    group_table = group_table[group_table["criterion"] == "weighted_degree"]
    group_pct = group_table.set_index("deployment_id")["pct_group_weight"]

    # Main neighbors (5 per candidate) in max100.
    # An edge appears twice: once seen from each end ("hub" is the candidate).
    edges = pd.read_csv(args.s204 / "edges_max100.csv")
    with_candidate = edges[edges["source"].isin(candidates) | edges["target"].isin(candidates)]
    source_is_hub = with_candidate[with_candidate["source"].isin(candidates)]
    source_is_hub = source_is_hub.rename(columns={"source": "hub", "target": "neighbor"})
    target_is_hub = with_candidate[with_candidate["target"].isin(candidates)]
    target_is_hub = target_is_hub.rename(columns={"target": "hub", "source": "neighbor"})
    long = pd.concat([source_is_hub, target_is_hub])
    long = long.sort_values(["hub", "shared_voters"], ascending=[True, False])
    long = long.groupby("hub").head(5)

    rows = []
    for node in candidates:
        neighbors = long[long["hub"] == node]
        if len(neighbors) > 0:
            top_neighbor = neighbors.iloc[0]
        else:
            top_neighbor = None

        # Same organization: one of its 5 main neighbors belongs to its organization
        organization = ORGANIZATION.get(node)
        same_org = False
        if organization is not None:
            for neighbor in neighbors["neighbor"]:
                if ORGANIZATION.get(neighbor) == organization:
                    same_org = True

        # Proportion: weight of the main neighbor / unique voters of the smaller of the two
        overlap = None
        neighbor_name = None
        neighbor_weight = None
        if top_neighbor is not None:
            neighbor_name = deployments["name"].get(top_neighbor["neighbor"])
            neighbor_weight = int(top_neighbor["shared_voters"])
            smaller = min(unique_voters.get(node, float("nan")),
                          unique_voters.get(top_neighbor["neighbor"], float("nan")))
            if not pd.isna(smaller) and smaller > 0:
                overlap = round(top_neighbor["shared_voters"] / smaller, 2)

        # Rank by unique voters (empty if the DAO has no data)
        if node in unique_voters_rank.index and not pd.isna(unique_voters_rank[node]):
            size_rank = int(unique_voters_rank[node])
        else:
            size_rank = None

        # Flags
        pct = group_pct.get(node)
        flag_filter = False
        if pct is not None and not pd.isna(pct) and pct >= GROUP_THRESHOLD:
            flag_filter = True

        flag_overlap = False
        if overlap is not None and overlap >= OVERLAP_THRESHOLD:
            if degree_rank[node] - weighted_ranks.at[node, "max100"] >= DEGREE_GAP:
                flag_overlap = True

        flag_size = False
        if size_rank is not None and size_rank <= TOP_SIZE:
            flag_size = True

        # One row per candidate (the order of the keys is the order of the columns)
        row = {
            "deployment_id": node,
            "name": deployments.at[node, "name"],
            "platform": deployments.at[node, "platform"],
        }
        for config in CONFIGS:
            row[f"rank_weighted_{config}"] = int(weighted_ranks.at[node, config])
        row["rank_weighted_diff"] = int(weighted_ranks.loc[node].max() - weighted_ranks.loc[node].min())
        row["rank_degree_max100"] = int(degree_rank[node])
        row["pct_group_weight_nolimit"] = pct
        row["unique_voters"] = unique_voters.get(node)
        row["rank_unique_voters"] = size_rank
        row["neighbor_1"] = neighbor_name
        row["neighbor_1_weight"] = neighbor_weight
        row["neighbor_1_proportion"] = overlap
        row["assigned_organization"] = organization
        row["F_filter"] = flag_filter
        row["F_overlap"] = flag_overlap
        row["F_size"] = flag_size
        row["F_org"] = same_org
        rows.append(row)

    table = pd.DataFrame(rows).set_index("deployment_id")
    table = table.sort_values("rank_weighted_max100")
    table.to_csv(args.s209 / "S2-09_hub_indicators.csv")

    # Short view on screen
    pd.set_option("display.width", 260)
    pd.set_option("display.max_colwidth", 20)
    pd.set_option("display.max_rows", 200)
    view_columns = ["name", "platform", "rank_weighted_nolimit", "rank_weighted_max200",
                    "rank_weighted_max100", "rank_weighted_max50", "pct_group_weight_nolimit",
                    "rank_unique_voters", "neighbor_1_proportion",
                    "F_filter", "F_overlap", "F_size", "F_org"]
    view = table[view_columns].copy()
    view.columns = ["name", "plat", "r_nolim", "r_200", "r_100", "r_50", "%group",
                    "r_uv", "overlap", "Ffil", "Fove", "Fsiz", "Forg"]
    print(f"{len(table)} candidates\n")
    print(view.to_string())


if __name__ == "__main__":
    main()
