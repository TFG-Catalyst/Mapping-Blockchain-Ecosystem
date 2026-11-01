"""
Run the whole pipeline with one command, from data/raw/ to the graph.

Steps, in order:
    1. Clean     data/raw/*.csv -> data/processed/*_clean.csv
    2. Nodes     deployments_clean.csv + votes_clean.csv -> nodes.csv
    3. Edges     votes_clean.csv -> edges.csv (shared voters)
    4. Jaccard   edges + DAO sizes -> edges_jaccard.csv
    5. Graph     nodes.csv + edges.csv -> NetworkX graph + sanity checks

max_daos is the only parameter of the network. It is defined once here and
passed to the edges and to Jaccard, so both always use the same value.

Run from the project root:
    python -m src.pipeline.run_pipeline                 # max_daos = 100
    python -m src.pipeline.run_pipeline --max-daos 200
    python -m src.pipeline.run_pipeline --skip-cleaning # reuse the *_clean.csv
"""

import argparse
import time

from src.pipeline.data_cleaner import run_cleaning
from src.pipeline.edge_generator import (
    DEFAULT_MAX_DAOS,
    filter_valid_voters,
    generate_dao_edges,
    load_unique_voter_dao_pairs,
    save_dao_edges,
)
from src.pipeline.graph_builder import build_graph
from src.pipeline.graph_sanity import graph_sanity_checks
from src.pipeline.jaccard_weights import compute_jaccard_edges, save_jaccard_edges
from src.pipeline.node_generator import generate_dao_nodes, save_dao_nodes


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the full pipeline: clean, nodes, edges, Jaccard, graph."
    )
    parser.add_argument(
        "--max-daos", type=int, default=DEFAULT_MAX_DAOS,
        help="Maximum number of DAOs a voter may vote in to create edges "
             f"(default: {DEFAULT_MAX_DAOS})"
    )
    parser.add_argument(
        "--skip-cleaning", action="store_true",
        help="Skip step 1 and reuse the existing *_clean.csv files "
             "(cleaning votes.csv is the slowest step)"
    )
    args = parser.parse_args()

    # A voter needs at least 2 DAOs to create an edge.
    if args.max_daos < 2:
        parser.error("--max-daos must be 2 or greater")

    return args


def run_step(number, title, function, *args):
    """Run one step, printing its title and how long it took."""
    print(f"\n[{number}/5] {title}")
    start = time.perf_counter()
    result = function(*args)
    print(f"      done in {time.perf_counter() - start:.1f} s")
    return result


def clean():
    run_cleaning()


def nodes():
    dao_nodes = generate_dao_nodes()
    save_dao_nodes(dao_nodes)
    print(f"      nodes: {len(dao_nodes)} "
          f"({(~dao_nodes['in_catalogue']).sum()} not in catalogue)")


def edges(max_daos):
    voter_dao_pairs = load_unique_voter_dao_pairs()
    valid_pairs = filter_valid_voters(voter_dao_pairs, max_daos=max_daos)
    dao_edges = generate_dao_edges(valid_pairs)
    save_dao_edges(dao_edges)
    print(f"      edges: {len(dao_edges)}, "
          f"total weight: {dao_edges['shared_voters'].sum()}")
    # The pairs are returned so Jaccard does not read votes_clean.csv again.
    return voter_dao_pairs, dao_edges


def jaccard(voter_dao_pairs, dao_edges, max_daos):
    jaccard_edges = compute_jaccard_edges(voter_dao_pairs, dao_edges, max_daos)
    output_file = save_jaccard_edges(jaccard_edges)
    print(f"      saved {len(jaccard_edges)} edges to {output_file.name}")


def graph():
    graph_sanity_checks(build_graph())


def main():
    args = parse_args()
    print(f"Pipeline parameters: max_daos = {args.max_daos}")
    start = time.perf_counter()

    if args.skip_cleaning:
        print("\n[1/5] Cleaning skipped (--skip-cleaning)")
    else:
        run_step(1, "Cleaning raw data", clean)

    run_step(2, "Generating nodes", nodes)
    voter_dao_pairs, dao_edges = run_step(
        3, f"Generating edges (max_daos = {args.max_daos})", edges, args.max_daos
    )
    run_step(4, "Adding Jaccard weights", jaccard,
             voter_dao_pairs, dao_edges, args.max_daos)
    run_step(5, "Building the graph", graph)

    print(f"\nPipeline finished in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
