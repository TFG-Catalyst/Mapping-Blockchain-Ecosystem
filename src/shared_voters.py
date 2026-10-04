"""
"Shared voters" relationship between DAOs (simplified version).

Idea: two DAOs are connected if the same wallet has voted in both.
Edge weight = number of distinct wallets that voted in both DAOs.
"""

import csv
from collections import Counter, defaultdict
from itertools import combinations

VOTES_CSV = "votes.csv"
OUTPUT_CSV = "shared_voters_edges.csv"
MAX_DAOS_PER_VOTER = 200  # wallets voting in more DAOs than this are ignored (bots/delegates)


def extract_address(voter):
    """Return the clean wallet address, depending on each platform's format."""
    voter = voter.strip()

    if "-voter-" in voter:                # Aragon: "<dao>-voter-<wallet>"
        voter = voter.split("-voter-")[-1]
    elif voter.startswith("eip155:"):     # Tally: "eip155:<chain>:<wallet>"
        voter = voter.split(":")[-1]

    # Ethereum addresses (0x...) are case-insensitive.
    # Solana addresses (Realms) are case-sensitive, so they are left untouched.
    return voter.lower() if voter.startswith("0x") else voter


def read_voters(path):
    """Return {wallet: set of DAOs where it has voted}."""
    voter_to_daos = defaultdict(set)
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["voter"] and row["deployment_id"]:
                wallet = extract_address(row["voter"])
                voter_to_daos[wallet].add(row["deployment_id"])
    return voter_to_daos


def build_edges(voter_to_daos):
    """Return {(dao_a, dao_b): number of shared wallets}."""
    weights = Counter()
    for daos in voter_to_daos.values():
        if 2 <= len(daos) <= MAX_DAOS_PER_VOTER:
            for pair in combinations(sorted(daos), 2):
                weights[pair] += 1
    return weights


def save_edges(weights, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["deployment_id_a", "deployment_id_b", "shared_voters_weight"])
        for (a, b), weight in weights.most_common():
            writer.writerow([a, b, weight])


def main():
    voters = read_voters(VOTES_CSV)
    multi_dao = sum(1 for daos in voters.values() if len(daos) > 1)
    print(f"Unique voters: {len(voters):,}")
    print(f"Voters in 2+ DAOs: {multi_dao:,} ({multi_dao / len(voters):.2%})")

    edges = build_edges(voters)
    nodes = {dao for pair in edges for dao in pair}
    print(f"Edges: {len(edges):,} | Connected DAOs: {len(nodes):,}")
    print(f"Mean weight: {sum(edges.values()) / len(edges):.2f} | max: {max(edges.values()):,}")

    save_edges(edges, OUTPUT_CSV)
    print(f"Saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
