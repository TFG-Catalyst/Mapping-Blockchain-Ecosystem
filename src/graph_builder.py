
from pathlib import Path

import networkx as nx
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def build_graph():
    nodes_path = PROCESSED_DATA_DIR / "nodes.csv"
    edges_path = PROCESSED_DATA_DIR / "edges.csv"

    if not nodes_path.exists():
        raise FileNotFoundError(
            f"Nodes file not found: {nodes_path}"
        )

    if not edges_path.exists():
        raise FileNotFoundError(
            f"Edges file not found: {edges_path}"
        )

    nodes = pd.read_csv(nodes_path)
    edges = pd.read_csv(edges_path)

    graph = nx.Graph()

    for _, row in nodes.iterrows():
        graph.add_node(
            row["deployment_id"],
            platform=row["platform"],
            name=row["name"],
            proposals_count=row["proposals_count"],
            unique_voters=row["unique_voters"],
            votes_count=row["votes_count"],
            in_catalogue=row["in_catalogue"]
        )

    valid_node_ids = set(nodes["deployment_id"])
    dropped_edges = 0

    for _, row in edges.iterrows():
        source = row["source"]
        target = row["target"]

        if source in valid_node_ids and target in valid_node_ids:
            graph.add_edge(
                source,
                target,
                shared_voters=row["shared_voters"]
            )
        else:
            dropped_edges += 1

    if dropped_edges > 0:
        missing_ids = (
            set(edges["source"]) | set(edges["target"])
        ) - valid_node_ids
        print(
            f"Warning: {dropped_edges} edges dropped because "
            f"{len(missing_ids)} endpoints are not nodes: {sorted(missing_ids)}"
        )

    return graph