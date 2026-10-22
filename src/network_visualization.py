import networkx as nx
import matplotlib.pyplot as plt
import argparse
import pandas as pd
from matplotlib.lines import Line2D

from graph_builder import build_graph

PLATFORM_COLORS = {
    "snapshot": "#1f77b4",
    "tally": "#ff7f0e",
    "aragon": "#2ca02c",
    "daohaus": "#d62728",
    "daostack": "#9467bd",
    "realms": "#8c564b",
}
UNKNOWN_COLOR = "#7f7f7f"
LABELLED_NODES = 10

def format_value(value):
    if value is None or pd.isna(value):
        return "Unknown"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"
    return str(value)


def node_name(graph, node_id):
    name = graph.nodes[node_id].get("name")
    if name is None or pd.isna(name):
        return node_id
    return name


def visualize_top_daos(graph, top_n=50, max_edges=100, min_shared_voters=1, platform = None):

    filtered_graph = graph

    if platform is not None:
        matching_nodes = [
            node_id
            for node_id, attributes in graph.nodes(data=True)
            if attributes.get("platform") == platform
        ]

        filtered_graph = graph.subgraph(matching_nodes)

    # Sort nodes by degree and select the most connected ones
    top_nodes = sorted(
        filtered_graph.degree,
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    top_node_ids = [node for node, degree in top_nodes]

    # Create a subgraph with the most connected DAOs
    subgraph = filtered_graph.subgraph(top_node_ids).copy()

   # Sort edges by number of shared voters
    eligible_edges = [
        (source, target, attributes)
        for source, target, attributes in subgraph.edges(data=True)
        if attributes["shared_voters"] >= min_shared_voters
    ]

    strongest_edges = sorted(
        eligible_edges,
        key=lambda x: x[2]["shared_voters"],
        reverse=True
    )[:max_edges]

    # Create a new graph containing only the strongest relationships
    strong_subgraph = nx.Graph()

    for u, v, data in strongest_edges:
        strong_subgraph.add_node(u, **subgraph.nodes[u])
        strong_subgraph.add_node(v, **subgraph.nodes[v])
        strong_subgraph.add_edge(
            u,
            v,
            shared_voters=data["shared_voters"]
        )

    subgraph = strong_subgraph
    if subgraph.number_of_edges() == 0:
        print("No relationships match the selected filters.")
        return

    # Remove nodes that became isolated after filtering
    subgraph.remove_nodes_from(list(nx.isolates(subgraph)))

    # Keep only the largest connected component of the selection
    components = list(nx.connected_components(subgraph))
    largest_component = max(components, key=len)
    omitted_components = len(components) - 1
    omitted_nodes = subgraph.number_of_nodes() - len(largest_component)
    subgraph = subgraph.subgraph(largest_component).copy()

    # Print visualization information
    print(f"Nodes visualized: {subgraph.number_of_nodes()}")
    print(f"Edges visualized: {subgraph.number_of_edges()}")
    print(f"Omitted: {omitted_nodes} nodes in {omitted_components} smaller components")

    # Calculate node positions
    pos = nx.spring_layout(
        subgraph,
        seed=42
    )

    # Draw the network
    plt.figure(figsize=(14, 10))

    node_ids = list(subgraph.nodes())

    # Node colour = platform; node size = degree in the full graph (square root scale)
    node_colors = [
        PLATFORM_COLORS.get(subgraph.nodes[node_id].get("platform"), UNKNOWN_COLOR)
        for node_id in node_ids
    ]
    degrees = [graph.degree[node_id] for node_id in node_ids]
    min_degree, max_degree = min(degrees), max(degrees)
    degree_range = max(max_degree - min_degree, 1)
    node_sizes = [
        100 + 900 * ((degree - min_degree) / degree_range) ** 0.5
        for degree in degrees
    ]

    node_collection = nx.draw_networkx_nodes(
        subgraph,
        pos,
        nodelist=node_ids,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors="white",
        linewidths=0.5
    )

    # Edge width = shared voters (square root scale)
    edge_ids = list(subgraph.edges())
    weights = [subgraph.edges[edge]["shared_voters"] for edge in edge_ids]
    min_weight, max_weight = min(weights), max(weights)
    weight_range = max(max_weight - min_weight, 1)
    edge_widths = [
        0.5 + 5.5 * ((weight - min_weight) / weight_range) ** 0.5
        for weight in weights
    ]

    edge_collection = nx.draw_networkx_edges(
        subgraph,
        pos,
        edgelist=edge_ids,
        width=edge_widths,
        edge_color="gray",
        alpha=0.6
    )

    # Names of the most connected DAOs only, to keep the view readable
    labelled_ids = sorted(
        node_ids, key=lambda node_id: graph.degree[node_id], reverse=True
    )[:LABELLED_NODES]
    nx.draw_networkx_labels(
        subgraph,
        pos,
        labels={node_id: node_name(subgraph, node_id) for node_id in labelled_ids},
        font_size=8,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1)
    )

    edge_collection.set_picker(5)

    node_collection.set_picker(5)

    ax = node_collection.axes

    info_box = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        fontsize=9,
        multialignment="left",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            edgecolor="gray",
            alpha=0.9
        ),
        zorder=10
    )
    info_box.set_visible(False)

    # Legend: one entry per platform present in the view
    platforms_shown = sorted(
        {str(subgraph.nodes[node_id].get("platform")) for node_id in node_ids}
    )
    legend_handles = [
        Line2D(
            [0], [0],
            marker="o",
            color="w",
            markerfacecolor=PLATFORM_COLORS.get(platform_name, UNKNOWN_COLOR),
            markersize=9,
            label=platform_name
        )
        for platform_name in platforms_shown
    ]
    ax.legend(handles=legend_handles, title="Platform", loc="upper right")

    # Counts of what is shown and what is left out
    ax.text(
        0.01,
        0.99,
        f"Shown: {subgraph.number_of_nodes():,} of {graph.number_of_nodes():,} DAOs, "
        f"{subgraph.number_of_edges():,} of {graph.number_of_edges():,} relationships\n"
        f"Omitted from the selection: {omitted_nodes} DAOs in {omitted_components} smaller components\n"
        f"Node size: degree in the full graph | Edge width: shared voters (both scaled within the view)",
        transform=ax.transAxes,
        va="top",
        fontsize=9
    )

    ax.text(
        0.01,
        0.01,
        "Click a node or an edge to see its details",
        transform=ax.transAxes,
        fontsize=8,
        color="gray"
    )

    def show_info(x, y, text):
        # Open the box towards the centre so it stays inside the figure
        x_min, x_max = ax.get_xlim()
        offset_x = -15 if x > (x_min + x_max) / 2 else 15
        info_box.xy = (x, y)
        info_box.xyann = (offset_x, 15)
        info_box.set_horizontalalignment("right" if offset_x < 0 else "left")
        info_box.set_text(text)
        info_box.set_visible(True)
        ax.figure.canvas.draw_idle()


    def on_node_click(event):
        if event.artist is not node_collection or len(event.ind) == 0:
            return

        node_id = node_ids[event.ind[0]]
        attributes = subgraph.nodes[node_id]

        details = (
            f"DAO: {node_name(subgraph, node_id)}\n"
            f"ID: {node_id}\n"
            f"Platform: {format_value(attributes.get('platform'))}\n"
            f"Unique voters (metadata): {format_value(attributes.get('unique_voters'))}\n"
            f"Votes (metadata): {format_value(attributes.get('votes_count'))}\n"
            f"Connections in full graph: {graph.degree[node_id]:,}"
        )

        x, y = pos[node_id]
        show_info(x, y, details)
        node_collection.figure.canvas.draw_idle()

    def on_edge_click(event):
        if event.artist is not edge_collection or len(event.ind) == 0:
            return

        # Give node selection priority when clicking near an endpoint.
        if node_collection.contains(event.mouseevent)[0]:
            return

        source, target = edge_ids[event.ind[0]]
        attributes = subgraph.edges[source, target]

        details = (
            f"DAO 1: {node_name(subgraph, source)}\n"
            f"DAO 2: {node_name(subgraph, target)}\n"
            f"Shared voters: {attributes['shared_voters']:,}"
        )

        x = (pos[source][0] + pos[target][0]) / 2
        y = (pos[source][1] + pos[target][1]) / 2
        show_info(x, y, details)
        edge_collection.figure.canvas.draw_idle()

    node_collection.figure.canvas.mpl_connect(
        "pick_event",
        on_node_click
    )
    node_collection.figure.canvas.mpl_connect(
        "pick_event",
        on_edge_click
    )


    plt.title(
        f"Largest connected component of the {max_edges} strongest relationships among the top {top_n} DAOs by degree\n"
        f"Platform: {platform if platform is not None else 'All'} | "
        f"Minimum shared voters: {min_shared_voters}"
    )   
    plt.axis("off")
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Explore the DAO graph with basic filters."
    )

    parser.add_argument("--top-n", type=int, default=50)
    parser.add_argument("--max-edges", type=int, default=100)
    parser.add_argument("--min-shared-voters", type=int, default=1)
    parser.add_argument(
        "--platform",
        choices=["all", "snapshot", "tally", "aragon"],
        default="all"
    )

    args = parser.parse_args()

    if args.top_n < 1:
        parser.error("--top-n must be at least 1")

    if args.max_edges < 1:
        parser.error("--max-edges must be at least 1")

    if args.min_shared_voters < 1:
        parser.error("--min-shared-voters must be at least 1")

    graph = build_graph()

    visualize_top_daos(
        graph,
        top_n=args.top_n,
        max_edges=args.max_edges,
        min_shared_voters=args.min_shared_voters, 
        platform=None if args.platform == "all" else args.platform
    )