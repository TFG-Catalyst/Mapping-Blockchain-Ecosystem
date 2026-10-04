import networkx as nx


def graph_sanity_checks(graph):

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    isolated_nodes = list(nx.isolates(graph))
    num_isolated_nodes = len(isolated_nodes)

    connected_components = list(nx.connected_components(graph))
    num_connected_components = len(connected_components)

    degrees = [degree for _, degree in graph.degree()]

    average_degree = sum(degrees) / len(degrees)

    max_degree = max(degrees)
    min_degree = min(degrees)

    print("GRAPH SANITY CHECKS")
    print("-------------------")
    print(f"Nodes: {num_nodes}")
    print(f"Edges: {num_edges}")
    print(f"Isolated nodes: {num_isolated_nodes}")
    print(f"Connected components: {num_connected_components}")
    print(f"Average degree: {average_degree:.2f}")
    print(f"Minimum degree: {min_degree}")
    print(f"Maximum degree: {max_degree}")
        
    self_loops = nx.number_of_selfloops(graph)

    largest_component = max(
        connected_components,
        key=len
    )

    print(f"Self-loops: {self_loops}")
    print(f"Largest connected component: {len(largest_component)} nodes")
if __name__ == "__main__":
    from graph_builder import build_graph

    graph = build_graph()
    graph_sanity_checks(graph)