import networkx as nx
import matplotlib.pyplot as plt

from graph_builder import build_graph


def visualize_top_daos(graph, top_n=50):

    # Sort nodes by degree and select the most connected ones
    top_nodes = sorted(
        graph.degree,
        key=lambda x: x[1],
        reverse=True
    )[:top_n]

    top_node_ids = [node for node, degree in top_nodes]

    # Create a subgraph with the most connected DAOs
    subgraph = graph.subgraph(top_node_ids).copy()

   # Sort edges by number of shared voters
    strongest_edges = sorted(
        subgraph.edges(data=True),
        key=lambda x: x[2]["shared_voters"],
        reverse=True
    )[:100]

    # Create a new graph containing only the strongest relationships
    strong_subgraph = nx.Graph()

    for u, v, data in strongest_edges:
        strong_subgraph.add_edge(
            u,
            v,
            shared_voters=data["shared_voters"]
        )

    subgraph = strong_subgraph

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

    nx.draw_networkx(
        subgraph,
        pos,
        with_labels=False,
        node_size=150,
        width=0.5
    )

    plt.title("100 Strongest Relationships among Top 50 DAOs by Degree")
    plt.axis("off")
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    graph = build_graph()
    visualize_top_daos(graph)