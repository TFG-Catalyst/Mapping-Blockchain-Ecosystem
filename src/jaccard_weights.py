"""
S2-05: Normalized edge weights using Jaccard similarity.

Idea
----
The current edge weight (shared_voters) counts how many wallets voted in
both DAOs. Big DAOs share many voters simply because they are big, so the
raw count favours size. 

Jaccard similarity corrects that:

jaccard(A, B) = |voters(A) ∩ voters(B)| / |voters(A) ∪ voters(B)|

And since |A ∪ B| = |A| + |B| - |A ∩ B|, we can compute it as:
            
jaccard(A, B) = shared_voters / (voters_A + voters_B - shared_voters)

Population 
----------
- The voter sets must come from the same votes used to build the edges (votes_clean.csv).
- Wallets that vote in more than MAX_DAOS DAOs are removed, exactly as in
edge_generator.py. 
- Wallets that vote in only one DAO cannot create edges, but they ARE part of that 
DAO's community, so they are counted in the DAO size (See COUNT_SINGLE_DAO_VOTERS below)

Output
------
data/processed/edges_jaccard.csv with one row per edge:
    [source, target, shared_voters, voters_source, voters_target,
    union_voters, jaccard]
Both measures are kept (shared_voters and jaccard), as the backlog asks.

Run from the project root:
    python src/jaccard_weights.py
"""

import random
import pandas as pd
 
from edge_generator import (
    PROCESSED_DATA_DIR, # Directory for processed data
    load_unique_voter_dao_pairs, # Function to load unique (voter, DAO) pairs from votes_clean.csv
    filter_valid_voters, # Function to filter voters based on MAX_DAOS
    generate_dao_edges, # Function to generate edges between DAOs based on shared voters
)

MAX_DAOS = 100 # Must be the same value used in edge_generator.py 

# True  -> DAO size counts every voter with <= MAX_DAOS DAOs (also those who only vote in that DAO). 
# False -> DAO size only counts voters with 2..MAX_DAOS DAOs (exactly the wallets that edge_generator.py keeps).
COUNT_SINGLE_DAO_VOTERS = True

# How many random edges to check by hand in the validation step.
RANDOM_PAIRS_TO_CHECK = 5


def select_population(voter_dao_pairs):
    """Return the (voter, DAO) pairs used to measure the size of each DAO."""
    daos_per_voter = voter_dao_pairs.groupby("voter")["deployment_id"].nunique()

    min_daos = 1 if COUNT_SINGLE_DAO_VOTERS else 2
    kept_voters = daos_per_voter[
        (daos_per_voter >= min_daos) & (daos_per_voter <= MAX_DAOS)
    ].index

    return voter_dao_pairs[voter_dao_pairs["voter"].isin(kept_voters)]


def count_voters_per_dao(population_pairs):
    """Number of distinct voters of each DAO: the |voters(A)| of the formula."""
    return population_pairs.groupby("deployment_id")["voter"].nunique()


def add_jaccard(edges, voters_per_dao):
    """Add the DAO sizes, the union and the Jaccard similarity to each edge."""
    edges = edges.copy()

    edges["voters_source"] = edges["source"].map(voters_per_dao)
    edges["voters_target"] = edges["target"].map(voters_per_dao)

    # |A ∪ B| = |A| + |B| - |A ∩ B|  (the shared voters would be counted twice)
    edges["union_voters"] = (
        edges["voters_source"] + edges["voters_target"] - edges["shared_voters"]
    )
    edges["jaccard"] = edges["shared_voters"] / edges["union_voters"]

    return edges


def validate_results(edges, population_pairs):
    """
    Check the results in three parts. The script stops if part A or B fails.

    A) Logic check on ALL edges: no impossible values.
    B) Recalculation by hand of some representative pairs, using Python sets
       instead of the counters, to confirm numerators and denominators.
    C) Comparison with the existing edges.csv (only prints a warning).
    """
    # ---- A) Logic check on all edges ----
    print("  A) Logic check on all edges")
    smaller_dao = edges[["voters_source", "voters_target"]].min(axis=1)
    bigger_dao = edges[["voters_source", "voters_target"]].max(axis=1)

    problems = {
        "DAO size missing": edges[["voters_source", "voters_target"]].isna().any(axis=1),
        "shared > smaller DAO": edges["shared_voters"] > smaller_dao,
        "union < bigger DAO": edges["union_voters"] < bigger_dao,
        "jaccard outside (0, 1]": (edges["jaccard"] <= 0) | (edges["jaccard"] > 1),
    }

    for name, failed in problems.items():
        print(f"     {name}: {int(failed.sum())} edges")
        if failed.any():
            raise ValueError(f"Check failed: {name}")

    # ---- B) Recalculation by hand of representative pairs ----
    print("  B) Hand recalculation of representative pairs")
    voters_of = population_pairs.groupby("deployment_id")["voter"].apply(set)

    # Strongest by raw count, strongest and weakest by Jaccard, plus random ones
    chosen = [
        edges["shared_voters"].idxmax(),
        edges["jaccard"].idxmax(),
        edges["jaccard"].idxmin(),
    ]
    random.seed(42)
    sample_size = min(RANDOM_PAIRS_TO_CHECK, len(edges))
    chosen += random.sample(list(edges.index), sample_size)
    chosen = list(dict.fromkeys(chosen))  # remove repeated edges, keep order

    rows = []
    for i in chosen:
        edge = edges.loc[i]
        a = voters_of[edge["source"]]
        b = voters_of[edge["target"]]

        shared_by_hand = len(a & b)
        union_by_hand = len(a | b)

        rows.append({
            "source": edge["source"],
            "target": edge["target"],
            "shared (table)": edge["shared_voters"],
            "shared (sets)": shared_by_hand,
            "union (table)": edge["union_voters"],
            "union (sets)": union_by_hand,
            "jaccard": round(edge["jaccard"], 4),
            "match": shared_by_hand == edge["shared_voters"]
            and union_by_hand == edge["union_voters"],
        })

    report = pd.DataFrame(rows)
    print(report.to_string(index=False))

    if not report["match"].all():
        raise ValueError("Some pairs do not match their hand calculation")

    # ---- C) Comparison with the existing edges.csv ----
    print("  C) Comparison with the existing edges.csv")
    existing_path = PROCESSED_DATA_DIR / "edges.csv"
    if not existing_path.exists():
        print("     edges.csv not found, skipping comparison")
        return

    existing = pd.read_csv(existing_path)
    same = (
        len(existing) == len(edges)
        and existing["shared_voters"].sum() == edges["shared_voters"].sum()
    )
    print(f"     edges.csv: {len(existing)} edges | recomputed: {len(edges)} edges")
    if not same:
        print("     WARNING: edges.csv does not match. Was it generated with "
              f"max_daos = {MAX_DAOS}? Regenerate it with edge_generator.py.")


if __name__ == "__main__":
    print("1. Loading unique (voter, DAO) pairs from votes_clean.csv")
    voter_dao_pairs = load_unique_voter_dao_pairs() # Returns a DataFrame with columns ["voter", "deployment_id"]

    print(f"2. Building the edges with max_daos = {MAX_DAOS} (same as edge_generator.py)")
    edge_pairs = filter_valid_voters(voter_dao_pairs, max_daos=MAX_DAOS)
    edges = generate_dao_edges(edge_pairs)

    print("3. Measuring the size of each DAO")
    population_pairs = select_population(voter_dao_pairs) 
    voters_per_dao = count_voters_per_dao(population_pairs)

    print("4. Computing Jaccard similarity")
    edges = add_jaccard(edges, voters_per_dao)

    print("5. Validating the results")
    validate_results(edges, population_pairs)

    output_file = PROCESSED_DATA_DIR / "edges_jaccard.csv"
    edges.to_csv(output_file, index=False)

    print(f"\nSaved {len(edges)} edges to {output_file}")
    print(edges["jaccard"].describe().to_string())
