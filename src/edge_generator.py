from pathlib import Path
from itertools import combinations
from collections import Counter

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def load_unique_voter_dao_pairs(chunksize=1_000_000):
    file_path = PROCESSED_DATA_DIR / "votes_clean.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed votes file not found: {file_path}"
        )

    chunks = []

    for chunk in pd.read_csv(
        file_path,
        usecols=["voter", "deployment_id"],
        chunksize=chunksize
    ):
        chunk = chunk.drop_duplicates()
        chunks.append(chunk)

    voter_dao_pairs = pd.concat(chunks, ignore_index=True)
    voter_dao_pairs = voter_dao_pairs.drop_duplicates()

    return voter_dao_pairs


def filter_valid_voters(voter_dao_pairs, max_daos=200):
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
    output_file = PROCESSED_DATA_DIR / "edges.csv"

    edges.to_csv(output_file, index=False)
if __name__ == "__main__":
    voter_dao_pairs = load_unique_voter_dao_pairs()

    valid_pairs = filter_valid_voters(voter_dao_pairs)

    edges = generate_dao_edges(valid_pairs)

    save_dao_edges(edges)

    print(f"Edges generated: {len(edges)}")