import networkx as nx
import pandas as pd

from src.paths import PROCESSED_DATA_DIR


def build_graph(include_jaccard=False):
    nodes_path = PROCESSED_DATA_DIR / "nodes.csv"
    edges_path = PROCESSED_DATA_DIR / "edges.csv"

    nodes = pd.read_csv(nodes_path)
    edges = pd.read_csv(edges_path)

    if include_jaccard:
        jaccard_path = PROCESSED_DATA_DIR / "edges_jaccard.csv"
        jaccard = pd.read_csv(
            jaccard_path,
            usecols=["source", "target", "shared_voters", "jaccard"],
        )

        edges = edges.merge(
            jaccard,
            on=["source", "target"],
            how="outer",
            suffixes=("", "_jaccard"),
            validate="one_to_one",
            indicator=True,
        )

        same_pairs = edges["_merge"].eq("both").all()
        same_weights = edges["shared_voters"].eq(
            edges["shared_voters_jaccard"]
        ).all()
        valid_jaccard = (
            edges["jaccard"].notna()
            & edges["jaccard"].gt(0)
            & edges["jaccard"].le(1)
        ).all()

        if not (same_pairs and same_weights and valid_jaccard):
            raise ValueError(
                "edges.csv and edges_jaccard.csv are inconsistent. "
                "Regenerate them using the same dataset and max_daos."
            )

        edges = edges.drop(
            columns=["shared_voters_jaccard", "_merge"]
        )

    graph = nx.Graph()

    for row in nodes.itertuples(index=False):
        graph.add_node(
            row.deployment_id,
            platform=row.platform,
            name=row.name,
            proposals_count=row.proposals_count,
            unique_voters=row.unique_voters,
            votes_count=row.votes_count,
            in_catalogue=row.in_catalogue,
        )

    valid_node_ids = set(nodes["deployment_id"])
    valid_edges = (
        edges["source"].isin(valid_node_ids)
        & edges["target"].isin(valid_node_ids)
    )
    dropped_edges = int((~valid_edges).sum())

    for row in edges.loc[valid_edges].itertuples(index=False):
        attributes = {"shared_voters": row.shared_voters}
        if include_jaccard:
            attributes["jaccard"] = row.jaccard
        graph.add_edge(row.source, row.target, **attributes)

    if dropped_edges:
        missing_ids = (
            set(edges["source"]) | set(edges["target"])
        ) - valid_node_ids
        print(
            f"Warning: {dropped_edges} edges dropped because "
            f"endpoints are missing from nodes.csv: {sorted(missing_ids)}"
        )

    return graph