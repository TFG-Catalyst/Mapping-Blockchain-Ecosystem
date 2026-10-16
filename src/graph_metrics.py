"""
S2-04, step 3: basic metrics of the DAO graph for each configuration of the
voter filter.

Replicates the logic of the team repository (graph_builder.py and
graph_sanity.py) but reading the files it is given, instead of the fixed
paths data/processed/nodes.csv and edges.csv. This way several graphs can
be compared without touching the team's code.

What it does, for each configuration:
  1. The nodes are all the DAOs in deployments.csv (lowercase ids, as
     data_cleaner.py does).
  2. Reads edges_<config>.csv (columns source, target, shared_voters).
  3. Like graph_builder.build_graph(): discards the edges whose endpoint is
     NOT a node (the S2-02 exclusions) and counts how many edges and how
     much weight are lost.
  4. Measures: nodes, edges, isolated nodes, connected components, largest
     component, degrees and edge weights.

Usage (from the repository root):
  python scripts/graph_metrics.py
  python scripts/graph_metrics.py --configs max50 max100

Options:
  --folder       folder with the edges_<config>.csv files (default results/S2-04)
  --deployments  DAO CSV (default data/raw/deployments.csv)
  --configs      configurations to measure (default: nolimit max200 max100 max50)
  --output       CSV with the metrics table
                 (default results/S2-04/S2-04_metrics_by_config.csv)

It only reads files; the only thing it writes is the metrics CSV.
"""

import argparse
import statistics
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

DEFAULT_CONFIGS = ["nolimit", "max200", "max100", "max50"]
DEFAULT_FOLDER = Path("results/S2-04")
DEFAULT_DEPLOYMENTS = Path("data/raw/deployments.csv")


def load_nodes(deployments_csv):
    """DAO ids in lowercase, like the team's clean_deployments()."""
    table = pd.read_csv(deployments_csv, usecols=["deployment_id"])
    return set(table["deployment_id"].astype("string").str.lower())


def build_graph(nodes, edges_csv):
    """
    Returns (graph, exclusion_info).
    Same rule as graph_builder.build_graph(): only the edges whose two
    endpoints are in the list of nodes get in.
    """
    edges = pd.read_csv(edges_csv)

    # An edge is valid if its two endpoints are nodes
    valid = edges["source"].isin(nodes) & edges["target"].isin(nodes)
    excluded = edges[valid == False]
    edges = edges[valid]

    # The graph starts with all the nodes (also the ones without edges)
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    # Each edge stores its number of shared voters under the name "shared_voters"
    graph.add_weighted_edges_from(
        zip(edges["source"], edges["target"], edges["shared_voters"]),
        weight="shared_voters",
    )

    # Ids that appear in the edges file but are not nodes
    excluded_ids = set(excluded["source"]) | set(excluded["target"])
    excluded_ids = excluded_ids - nodes

    info = {
        "edges_in_csv": len(excluded) + len(edges),
        "edges_excluded_s2_02": len(excluded),
        "weight_excluded_s2_02": int(excluded["shared_voters"].sum()),
        "excluded_ids": sorted(excluded_ids),
    }
    return graph, info


def measure(graph, info):
    """Metrics of graph_sanity_checks() plus weight statistics."""
    # Size of each connected component, from largest to smallest
    components = []
    for component in nx.connected_components(graph):
        components.append(len(component))
    components.sort(reverse=True)

    # Nodes with no edges
    isolated = 0
    for node in nx.isolates(graph):
        isolated += 1

    # Degree of each node and weight of each edge
    degrees = []
    for node, degree in graph.degree():
        degrees.append(degree)
    weights = []
    for node_a, node_b, data in graph.edges(data=True):
        weights.append(data["shared_voters"])
    n_edges = len(weights)

    # Edges with at least 2 shared voters
    edges_weight_ge_2 = 0
    for weight in weights:
        if weight >= 2:
            edges_weight_ge_2 += 1

    # Components with a single node
    single_node_components = 0
    for size in components:
        if size == 1:
            single_node_components += 1

    return {
        "nodes": graph.number_of_nodes(),
        "isolated_nodes": isolated,
        "connected_nodes": graph.number_of_nodes() - isolated,
        "edges": n_edges,
        "edges_excluded_s2_02": info["edges_excluded_s2_02"],
        "weight_excluded_s2_02": info["weight_excluded_s2_02"],
        "edges_weight_ge_2": edges_weight_ge_2,
        "pct_edges_weight_ge_2": round(100 * edges_weight_ge_2 / n_edges, 2),
        "total_weight": sum(weights),
        "mean_weight": round(sum(weights) / n_edges, 2),
        "median_weight": statistics.median(weights),
        "max_weight": max(weights),
        "mean_degree": round(sum(degrees) / len(degrees), 2),
        "max_degree": max(degrees),
        "components": len(components),
        "largest_component": components[0],
        "single_node_components": single_node_components,
        "self_loops": nx.number_of_selfloops(graph),
    }


def parse_arguments():
    parser = argparse.ArgumentParser(description="Graph metrics by configuration (S2-04).")
    parser.add_argument("--folder", type=Path, default=DEFAULT_FOLDER)
    parser.add_argument("--deployments", type=Path, default=DEFAULT_DEPLOYMENTS)
    parser.add_argument("--configs", nargs="+", default=DEFAULT_CONFIGS)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main():
    args = parse_arguments()
    if args.output:
        output = args.output
    else:
        output = args.folder / "S2-04_metrics_by_config.csv"

    nodes = load_nodes(args.deployments)
    print(f"Nodes (DAOs in deployments.csv): {len(nodes):,}", flush=True)

    rows = []
    for config in args.configs:
        path = args.folder / f"edges_{config}.csv"
        if not path.exists():
            sys.exit(f"ERROR: {path} does not exist")

        graph, info = build_graph(nodes, path)
        row = {"config": config}
        row.update(measure(graph, info))
        rows.append(row)

        print(f"\n== {config} ==  (ids excluded for not being a node: "
              f"{len(info['excluded_ids'])})", flush=True)
        for name, value in row.items():
            if name == "config":
                continue
            if isinstance(value, int):
                print(f"  {name:28s} {value:>12,}")
            else:
                print(f"  {name:28s} {value:>12}")

    pd.DataFrame(rows).to_csv(output, index=False)
    print(f"\nTable saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
