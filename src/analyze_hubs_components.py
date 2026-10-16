"""
S2-04, step 4: hubs, connected components and comparison between
configurations.

For each configuration of the voter filter (nolimit, max200, max100, max50)
and using the edge CSVs in results/S2-04/:

  1. Hubs: the nodes with the most neighbors ("degree") and with the most
     accumulated weight ("weighted degree" = sum of shared_voters of their
     edges).
  2. How much the top of hubs changes between configurations (nodes in
     common and Spearman correlation between the degrees).
  3. Connected components: the sizes of the largest ones and whether the
     largest component contains the same nodes.
  4. Edge comparison with the reference configuration (max200, the team's
     current one): which ones disappear, which ones appear and how many
     weights change.

Uses the same rule as the team's graph_builder.py: an edge only counts if
its two endpoints are nodes of deployments.csv (lowercase ids).

Usage (from the repository root):
  python scripts/analyze_hubs_components.py

Options: --folder, --deployments, --configs, --reference, --top.
Writes to the edges folder:
  S2-04_hubs_by_config.csv         top N hubs per configuration and criterion
  S2-04_nodes_by_config.csv        degree and weighted degree of each node in each configuration
  S2-04_components_by_config.csv   sizes of the 10 largest components
  S2-04_edge_comparison.csv        edges that appear/disappear and weights that change
"""

import argparse
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

DEFAULT_CONFIGS = ["nolimit", "max200", "max100", "max50"]
DEFAULT_REFERENCE = "max200"
DEFAULT_TOP = 20
TOP_SIZES_TO_COMPARE = [10, 20, 50, 100]
CRITERIA = ["degree", "weighted_degree"]


def load_nodes(deployments_csv):
    """Table of DAOs with lowercase id (like the team's clean_deployments)."""
    table = pd.read_csv(deployments_csv, usecols=["deployment_id", "platform", "name"])
    table["deployment_id"] = table["deployment_id"].astype("string").str.lower()
    table = table.drop_duplicates("deployment_id")
    return table.set_index("deployment_id")


def load_edges(folder, config, node_ids):
    """Edges of the configuration that satisfy the graph_builder rule."""
    edges = pd.read_csv(folder / f"edges_{config}.csv")
    valid = edges["source"].isin(node_ids) & edges["target"].isin(node_ids)
    return edges[valid].reset_index(drop=True)


def degrees(edges):
    """Degree (number of neighbors) and weighted degree (sum of weights) of each node."""
    # Each edge counts for its two ends, so we stack both columns
    as_source = edges[["source", "shared_voters"]].rename(columns={"source": "node"})
    as_target = edges[["target", "shared_voters"]].rename(columns={"target": "node"})
    both_ends = pd.concat([as_source, as_target])

    by_node = both_ends.groupby("node")["shared_voters"]
    return pd.DataFrame({"degree": by_node.size(), "weighted_degree": by_node.sum()})


def top_nodes(degree_table, criterion, how_many):
    """The `how_many` nodes with the highest value of the criterion (ties keep their order)."""
    values = degree_table[criterion].sort_values(ascending=False, kind="stable")
    return values.head(how_many)


def components(edges, node_ids):
    """List of components (sets of nodes), from largest to smallest."""
    graph = nx.Graph()
    graph.add_nodes_from(node_ids)
    graph.add_edges_from(zip(edges["source"], edges["target"]))
    return sorted(nx.connected_components(graph), key=len, reverse=True)


def compare_edges(ref, other):
    """Compares two edge tables (same key source,target)."""
    merged = ref.merge(other, on=["source", "target"], how="outer",
                       suffixes=("_ref", "_other"), indicator=True)
    common = merged[merged["_merge"] == "both"]
    changed = common["shared_voters_ref"] != common["shared_voters_other"]
    ratio = common["shared_voters_other"] / common["shared_voters_ref"]

    if changed.any():
        median_ratio = round(float(ratio[changed].median()), 3)
    else:
        median_ratio = None

    return {
        "edges_ref": len(ref),
        "edges_other": len(other),
        "only_in_ref": int((merged["_merge"] == "left_only").sum()),
        "only_in_other": int((merged["_merge"] == "right_only").sum()),
        "common": len(common),
        "common_with_different_weight": int(changed.sum()),
        "pct_common_with_different_weight": round(100 * changed.mean(), 2),
        "median_weight_ratio_in_changed": median_ratio,
        "total_weight_ref": int(ref["shared_voters"].sum()),
        "total_weight_other": int(other["shared_voters"].sum()),
    }


def parse_arguments():
    parser = argparse.ArgumentParser(description="Hubs, components and comparison (S2-04 step 4).")
    parser.add_argument("--folder", type=Path, default=Path("results/S2-04"))
    parser.add_argument("--deployments", type=Path, default=Path("data/raw/deployments.csv"))
    parser.add_argument("--configs", nargs="+", default=DEFAULT_CONFIGS)
    parser.add_argument("--reference", default=DEFAULT_REFERENCE)
    parser.add_argument("--top", type=int, default=DEFAULT_TOP)
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.reference not in args.configs:
        sys.exit("ERROR: the reference must be among the configurations.")
    nodes = load_nodes(args.deployments)
    ids = set(nodes.index)
    ref = args.reference

    # Edges and degrees of each configuration
    edges = {}
    deg = {}
    for config in args.configs:
        edges[config] = load_edges(args.folder, config, ids)
        deg[config] = degrees(edges[config])

    # ---- Table per node (for later steps and S2-09) ----
    all_nodes = set()
    for config in args.configs:
        all_nodes = all_nodes | set(deg[config].index)
    union = sorted(all_nodes)

    table = nodes.loc[union, ["platform", "name"]].copy()
    for config in args.configs:
        table[f"degree_{config}"] = deg[config]["degree"].reindex(union).fillna(0).astype(int)
        table[f"weighted_degree_{config}"] = deg[config]["weighted_degree"].reindex(union).fillna(0).astype(int)
    table.index.name = "deployment_id"
    table.to_csv(args.folder / "S2-04_nodes_by_config.csv")

    # ---- 1. Hubs by configuration ----
    hub_rows = []
    for config in args.configs:
        for criterion in CRITERIA:
            top = top_nodes(deg[config], criterion, args.top)
            position = 0
            for node in top.index:
                position += 1
                hub_rows.append({
                    "config": config,
                    "criterion": criterion,
                    "position": position,
                    "deployment_id": node,
                    "platform": nodes.at[node, "platform"],
                    "name": nodes.at[node, "name"],
                    "degree": int(deg[config].at[node, "degree"]),
                    "weighted_degree": int(deg[config].at[node, "weighted_degree"]),
                })
    pd.DataFrame(hub_rows).to_csv(args.folder / "S2-04_hubs_by_config.csv", index=False)

    for criterion in CRITERIA:
        print(f"\n===== HUBS by {criterion}: top 15 of {ref} and their position in each configuration =====")

        # Position of every node in each configuration (1 = the largest)
        positions = {}
        for config in args.configs:
            positions[config] = deg[config][criterion].rank(ascending=False, method="min")

        for node in top_nodes(deg[ref], criterion, 15).index:
            name = str(nodes.at[node, "name"])[:28]
            platform = nodes.at[node, "platform"]
            position_texts = []
            for config in args.configs:
                position = int(positions[config].get(node, 0))
                if position == 0:
                    shown = "-"     # the node has no edges in this configuration
                else:
                    shown = str(position)
                position_texts.append(f"{config}:{shown:>5}")
            value = int(deg[ref].at[node, criterion])
            print(f"  {name:28s} {platform:9s} {node[:18]:18s} "
                  f"{'  '.join(position_texts)}   {criterion}({ref})={value:,}")

        print(f"\n  Nodes in common of the top-N with {ref}:")
        header = "  " + "N".rjust(5)
        for config in args.configs:
            if config != ref:
                header += config.rjust(12)
        print(header)
        for n in TOP_SIZES_TO_COMPARE:
            top_ref = set(top_nodes(deg[ref], criterion, n).index)
            line = ""
            for config in args.configs:
                if config == ref:
                    continue
                top_config = set(top_nodes(deg[config], criterion, n).index)
                in_common = len(top_ref & top_config)
                line += f"{in_common:>8d}/{n:<3d}"
            print(f"  {n:>5d}" + line)

    print("\n===== Spearman correlation between configurations (nodes with edges in both) =====")
    for criterion in CRITERIA:
        columns = {}
        for config in args.configs:
            columns[config] = deg[config][criterion]
        values = pd.DataFrame(columns).dropna()
        print(f"\n  {criterion} ({len(values):,} nodes with edges in all 4):")
        print(values.corr(method="spearman").round(4).to_string())

    # ---- 3. Components ----
    print("\n===== CONNECTED COMPONENTS =====")
    comp = {}
    for config in args.configs:
        comp[config] = components(edges[config], ids)

    component_rows = []
    for config in args.configs:
        sizes = []
        for component in comp[config]:
            sizes.append(len(component))
        with_2_or_more = 0
        for size in sizes:
            if size >= 2:
                with_2_or_more += 1
        print(f"  {config:10s} components={len(sizes):>7,}  with >=2 nodes={with_2_or_more:>5,}  "
              f"largest: {sizes[:6]}")
        position = 0
        for size in sizes[:10]:
            position += 1
            component_rows.append({"config": config, "position": position, "nodes": size})
    pd.DataFrame(component_rows).to_csv(args.folder / "S2-04_components_by_config.csv", index=False)

    largest_ref = comp[ref][0]
    print(f"\n  Largest component vs that of {ref} ({len(largest_ref):,} nodes):")
    for config in args.configs:
        if config == ref:
            continue
        other = comp[config][0]
        print(f"   {config:10s} nodes in common={len(largest_ref & other):>7,}  "
              f"only in {ref}={len(largest_ref - other):>5,}  "
              f"only in {config}={len(other - largest_ref):>5,}")

    # ---- 4. Edges vs reference ----
    print(f"\n===== EDGES compared with {ref} =====")
    comparison_rows = []
    for config in args.configs:
        if config == ref:
            continue
        result = compare_edges(edges[ref], edges[config])

        row = {"reference": ref, "config": config}
        row.update(result)
        comparison_rows.append(row)

        print(f"\n  {config}:")
        for name, value in result.items():
            if isinstance(value, int):
                print(f"    {name:42s} {value:>12,}")
            else:
                print(f"    {name:42s} {value:>12}")
    pd.DataFrame(comparison_rows).to_csv(args.folder / "S2-04_edge_comparison.csv", index=False)
    print(f"\nFiles saved to {args.folder.resolve()}")


if __name__ == "__main__":
    main()
