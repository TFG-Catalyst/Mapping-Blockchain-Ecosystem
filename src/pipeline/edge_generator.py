from itertools import combinations
from collections import Counter

import pandas as pd

from src.paths import PROCESSED_DATA_DIR

# Maximum number of DAOs a voter may vote in to create edges. Voters above it
# are treated as outliers (S2-03, S2-04). This is the only place where the
# default is defined: jaccard_weights.py and run_pipeline.py import it.
DEFAULT_MAX_DAOS = 100

def _merge_unique_pairs(unique_pairs, new_chunks):
    """Add new chunks to the pairs kept so far and drop repeated pairs."""
    parts = new_chunks if unique_pairs is None else [unique_pairs] + new_chunks
    return pd.concat(parts, ignore_index=True).drop_duplicates()


def load_unique_voter_dao_pairs(chunksize=1_000_000, merge_every=10):
    """
    Unique (voter, deployment_id) pairs of votes_clean.csv.

    The file is read in chunks. Every `merge_every` chunks the pending chunks
    are merged into the pairs kept so far and the repeated pairs are dropped.
    This way memory holds the unique pairs plus at most `merge_every` chunks,
    instead of every chunk of the file at once (needed for the ~15 GB votes
    file of the corrected Zenodo version, S3-03). The result is the same as
    concatenating all the chunks and dropping duplicates once at the end.
    """
    file_path = PROCESSED_DATA_DIR / "votes_clean.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed votes file not found: {file_path}"
        )

    unique_pairs = None
    pending = []

    for chunk in pd.read_csv(
        file_path,
        usecols=["voter", "deployment_id"],
        chunksize=chunksize
    ):
        pending.append(chunk.drop_duplicates())

        if len(pending) >= merge_every:
            unique_pairs = _merge_unique_pairs(unique_pairs, pending)
            pending = []

    if pending or unique_pairs is None:
        unique_pairs = _merge_unique_pairs(unique_pairs, pending)

    return unique_pairs


def filter_valid_voters(voter_dao_pairs, max_daos=DEFAULT_MAX_DAOS):
    dao_count_per_voter = (
        voter_dao_pairs
        .groupby("voter")["deployment_id"]
        .nunique()
    )

    valid_voters = dao_count_per_voter[
        (dao_count_per_voter >= 2) &
        (dao_count_per_voter <= max_daos)
    ].index

    return voter_dao_pairs[
        voter_dao_pairs["voter"].isin(valid_voters)
    ].copy()


def generate_dao_edges(valid_pairs):
    edge_counter = Counter()

    grouped = valid_pairs.groupby("voter")["deployment_id"]

    for _, dao_group in grouped:
        daos = sorted(dao_group.unique())

        for dao_a, dao_b in combinations(daos, 2):
            edge_counter[(dao_a, dao_b)] += 1

    edges = pd.DataFrame(
        [
            (source, target, shared_voters)
            for (source, target), shared_voters in edge_counter.items()
        ],
        columns=["source", "target", "shared_voters"]
    )

    return edges

#Export
def save_dao_edges(edges):
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DATA_DIR / "edges.csv"
    edges.to_csv(output_file, index=False)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate data/processed/edges.csv from votes_clean.csv"
    )
    parser.add_argument(
        "--max-daos", type=int, default=DEFAULT_MAX_DAOS,
        help=f"Maximum DAOs per voter (default: {DEFAULT_MAX_DAOS})"
    )
    args = parser.parse_args()

    voter_dao_pairs = load_unique_voter_dao_pairs()

    valid_pairs = filter_valid_voters(voter_dao_pairs, max_daos=args.max_daos)

    edges = generate_dao_edges(valid_pairs)

    save_dao_edges(edges)

    print(f"Edges generated: {len(edges)} (max_daos = {args.max_daos})")