import networkx as nx
import matplotlib.pyplot as plt
import argparse

from graph_builder import build_graph


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

    # Print visualization information
    print(f"Nodes visualized: {subgraph.number_of_nodes()}")
    print(f"Edges visualized: {subgraph.number_of_edges()}")

    # Calculate node positions
    pos = nx.spring_layout(
        subgraph,
        seed=42
    )

    # Draw the network
    plt.figure(figsize=(14, 10))

    node_ids = list(subgraph.nodes())

    node_collection = nx.draw_networkx_nodes(
        subgraph,
        pos,
        nodelist=node_ids,
        node_size=150
    )

    edge_ids = list(subgraph.edges())

    edge_collection = nx.draw_networkx_edges(
        subgraph,
        pos,
        edgelist=edge_ids,
        width=0.5
    )

    edge_collection.set_picker(5)

    node_collection.set_picker(5)

    ax = node_collection.axes

    info_box = ax.text(
        0.02,
        0.98,
        "Click a node to see its details",
        transform=ax.transAxes,
        va="top",
        fontsize=9,
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            edgecolor="gray",
            alpha=0.9
        )
    )


    def on_node_click(event):
        if event.artist is not node_collection or len(event.ind) == 0:
            return

        node_id = node_ids[event.ind[0]]
        attributes = subgraph.nodes[node_id]

        details = (
            f"DAO: {attributes.get('name', node_id)}\n"
            f"ID: {node_id}\n"
            f"Platform: {attributes.get('platform', 'Unknown')}\n"
            f"Unique voters: {attributes.get('unique_voters', 'Unknown')}\n"
            f"Votes: {attributes.get('votes_count', 'Unknown')}\n"
            f"Connections in full graph: {graph.degree[node_id]}"
        )

        info_box.set_text(details)
        node_collection.figure.canvas.draw_idle()

    def on_edge_click(event):
        if event.artist is not edge_collection or len(event.ind) == 0:
            return

        # Give node selection priority when clicking near an endpoint.
        if node_collection.contains(event.mouseevent)[0]:
            return

        source, target = edge_ids[event.ind[0]]
        attributes = subgraph.edges[source, target]

        source_name = subgraph.nodes[source].get("name", source)
        target_name = subgraph.nodes[target].get("name", target)

        details = (
            f"DAO 1: {source_name}\n"
            f"DAO 2: {target_name}\n"
            f"Shared voters: {attributes['shared_voters']}"
        )

        info_box.set_text(details)
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
            f"Up to {max_edges} Strongest Relationships "
            f"among Top {top_n} DAOs by Degree"
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