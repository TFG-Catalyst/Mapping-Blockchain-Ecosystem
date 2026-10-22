
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MIN_SHARED_VOTERS = 10
TOP_EDGES = 20


def load_comparison_edges():
    edges = pd.read_csv(
        PROCESSED_DIR / "edges_jaccard.csv",
        dtype={"source": str, "target": str},
    )

    eligible = edges.loc[
        edges["shared_voters"] >= MIN_SHARED_VOTERS
    ].copy()

    if eligible.empty:
        raise ValueError("No edges match the minimum shared voters.")

    top_raw = eligible.nlargest(TOP_EDGES, "shared_voters")
    top_normalized = eligible.sort_values(
        ["jaccard", "shared_voters", "source", "target"],
        ascending=[False, False, True, True],
    ).head(TOP_EDGES)

    selected = (
        pd.concat([top_raw, top_normalized])
        .drop_duplicates(subset=["source", "target"])
        .reset_index(drop=True)
    )

    return selected

def build_comparison_graph(selected):
    nodes = pd.read_csv(
        PROCESSED_DIR / "nodes.csv",
        dtype={"deployment_id": str},
    ).set_index("deployment_id")

    graph = nx.from_pandas_edgelist(
        selected,
        source="source",
        target="target",
        edge_attr=["shared_voters", "jaccard"],
    )

    for node_id in graph.nodes:
        name = node_id

        if node_id in nodes.index:
            candidate = nodes.at[node_id, "name"]
            if pd.notna(candidate) and str(candidate).strip():
                name = str(candidate)

        # Shorten addresses or long names for display.
        label = name if len(name) <= 24 else f"{name[:12]}…{name[-6:]}"
        graph.nodes[node_id]["label"] = f"{label}\n[{node_id[-8:]}]"

    return graph


def plot_comparison(graph):
    # Reuse exactly the same positions in both panels.
    positions = nx.spring_layout(graph, seed=42, weight=None)
    edge_ids = list(graph.edges())
    labels = nx.get_node_attributes(graph, "label")

    fig, axes = plt.subplots(figsize=(22, 11), ncols=2)

    panels = [
        ("shared_voters", "Raw weight: shared voters"),
        ("jaccard", "Normalized weight: Jaccard"),
    ]

    for ax, (metric, title) in zip(axes, panels):
        values = [graph.edges[edge][metric] for edge in edge_ids]
        maximum = max(values)

        # Width is proportional to the square root of the weight.
        widths = [0.3 + 5 * (value / maximum) ** 0.5 for value in values]

        nx.draw_networkx_nodes(
            graph,
            positions,
            node_color="#90caf9",
            node_size=180,
            ax=ax,
        )
        nx.draw_networkx_edges(
            graph,
            positions,
            edgelist=edge_ids,
            width=widths,
            edge_color="#455a64",
            alpha=0.7,
            ax=ax,
        )
        nx.draw_networkx_labels(
            graph,
            positions,
            labels=labels,
            font_size=6,
            ax=ax,
        )

        # Show the values represented by three example widths.
        legend_values = [maximum / 100, maximum / 10, maximum]
        handles = [
            plt.Line2D(
                [0], [0],
                color="#455a64",
                linewidth=0.3 + 5 * (value / maximum) ** 0.5,
                label=(
                    f"{value:,.0f}"
                    if metric == "shared_voters"
                    else f"{value:.3f}"
                ),
            )
            for value in legend_values
        ]

        ax.legend(handles=handles, title=metric, loc="upper left")
        ax.set_title(title)
        ax.set_axis_off()

    fig.suptitle(
        f"Same relationships and positions — "
        f"at least {MIN_SHARED_VOTERS} shared voters\n"
        f"Union of top {TOP_EDGES} by count and top {TOP_EDGES} by Jaccard"
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    output_dir = PROJECT_ROOT / "docs" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "S2-14_raw_vs_jaccard.png"

    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Saved figure: {output_path}")
    plt.show()

if __name__ == "__main__":
    selected = load_comparison_edges()

    print(f"Selected relationships: {len(selected)}")
    print(
        selected[
            ["source", "target", "shared_voters", "jaccard"]
        ].to_string(index=False)
    )
    graph = build_comparison_graph(selected)
    plot_comparison(graph)