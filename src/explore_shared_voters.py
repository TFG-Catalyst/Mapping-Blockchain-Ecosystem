"""
Exploration of the "shared voters" relationship between DAOs
================================================================
TFG - Sprint 1 (Track A: exploration and network relationships)

What this script does:
1. Loads votes.csv.
2. Extracts the real voter address from the `voter` field
   (observed format: "<prefix>-voter-<address>").
3. Builds, for each voter, the set of deployment_id (DAOs) in which they
   have voted.
4. Counts, for each pair of DAOs, how many voters they have in common
   (this is exactly the edge definition: weight = number of shared
   addresses).
5. Prints statistics to decide whether the relationship is viable with real
   data: how many voters vote in more than one DAO, how many DAOs end up
   connected, the weight distribution, etc.
6. Saves the resulting edge table to a CSV.

How to use it (run from the repository root):
- Run: python scripts/explore_shared_voters.py
  Options: --max-daos N (0 = no limit) and --output path.csv
  (e.g.: python scripts/explore_shared_voters.py --max-daos 50)
  --format team (S2-04): saves the edges in the format of the team
  repository (columns source, target, shared_voters; lowercase ids).
  With --format original the CSV is the Sprint 1 one.
  NOTE: since S2-04 the default threshold is 100 (it used to be 200). To
  reproduce Sprint 1 you must pass --max-daos 200 explicitly.
- Cache: the first run reads votes.csv and saves voters_cache.pkl in
  data/processed/; later runs reuse it as long as votes.csv does not change
  (delete the .pkl to force a recomputation).

Notes / decisions already taken:
- `weight` (voting power) is not used as the edge weight because, according
  to Rodrigo's data dictionary, it is not comparable across DAOs (token
  units, not verified). The edge weight is the NUMBER OF SHARED VOTERS
  (a count), not voting power.
- Equivalent DAOs across platforms are not deduplicated (candidate
  relationship "same organization on several platforms"). If two DAOs are
  really the same entity on Snapshot and on Tally, they will count here as
  two different nodes. This is a known simplification for Sprint 1.
- "Promiscuous" voters that appear in an unrealistic number of DAOs
  (possible bot, professional delegate or data error) are excluded through
  the --max-daos parameter, to prevent them from causing a combinatorial
  explosion of pairs and from distorting the graph with meaningless
  connections.
"""

import argparse
import csv
import pickle
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

# ----------------------------------------------------------------------
# CONFIGURATION - ADJUST THESE PATHS
# ----------------------------------------------------------------------
VOTES_CSV = Path("data/raw/votes.csv")
DEPLOYMENTS_CSV = Path("data/raw/deployments.csv")  # only used for DAO names

# Prefix of the output CSV; the threshold used is appended to it
# (e.g. edges_shared_voters_max100.csv).
OUTPUT_PREFIX = "edges_shared_voters"

# File where the result of reading votes.csv is stored (to avoid re-reading it every time).
VOTERS_CACHE = Path("data/processed/voters_cache.pkl")

# Default threshold: if a voter appears in more DAOs than this, they are
# excluded from the edge computation (atypical pattern, see S2-03).
# It is only the default value: it can be changed when running with
# --max-daos N (0 = exclude nobody), without touching the code.
# S2-04: working configuration = 100 (in Sprint 1 it was 200).
# Justification in docs/S2-04_graph_sensitivity_to_the_filter.md.
DEFAULT_MAX_DAOS_PER_VOTER = 100

# Minimum number of shared voters for an edge to "count" as significant in
# the statistics (it does not filter the output CSV, it only affects the
# printed summaries).
MIN_SIGNIFICANT_WEIGHT = 2


# ----------------------------------------------------------------------
# 1. Extract the real voter address
# ----------------------------------------------------------------------
def extract_address(voter_raw):
    """
    The `voter` field has a DIFFERENT format depending on the platform
    (checked with a real sample from each one):

    - aragon:            "<deployment_id>-voter-<address>"
    - daohaus/daostack/
      snapshot:          "<address>" (already given directly)
    - tally:             "eip155:<chain_id>:<address>" (CAIP-10 prefix)
    - realms:            Solana address in base58 (NOT 0x format,
                         it is case-sensitive, it must not be touched)

    We lowercase ONLY Ethereum-style addresses (0x...), because they are
    case-insensitive (checksum). Non-0x addresses (e.g. Solana on realms)
    are left as they are so as not to corrupt the identity.
    """
    voter_raw = voter_raw.strip()

    # Format "<deployment_id>-voter-<address>"
    marker = "-voter-"
    position = voter_raw.find(marker)
    if position != -1:
        address = voter_raw[position + len(marker):].strip()
        if address.startswith("0x"):
            return address.lower()
        return address

    # Format "eip155:<chain_id>:<address>"
    if voter_raw.startswith("eip155:"):
        parts = voter_raw.split(":")
        address = parts[-1].strip()
        if address.startswith("0x"):
            return address.lower()
        return address

    # Plain Ethereum address
    if voter_raw.startswith("0x"):
        return voter_raw.lower()

    # Not a known 0x format (e.g. Solana address from realms): do not touch.
    return voter_raw


# ----------------------------------------------------------------------
# 2. Load votes.csv and build voter -> set(deployment_id)
# ----------------------------------------------------------------------
def detect_format(voter_raw):
    """Classifies the format of the voter field, for reporting purposes only."""
    if "-voter-" in voter_raw:
        return "aragon (deployment-voter-address)"
    if voter_raw.startswith("eip155:"):
        return "tally (eip155:chain:address)"
    if voter_raw.startswith("0x"):
        return "plain 0x (daohaus/daostack/snapshot)"
    return "other / non-0x (e.g. realms/Solana)"


def build_voter_to_daos(votes_csv):
    """Reads votes.csv and returns the dictionary {wallet: set of deployment_id}."""
    voter_to_daos = {}
    total_rows = 0
    formats = Counter()
    rows_by_platform = Counter()

    with votes_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Check that the columns we need are in the file
        columns = reader.fieldnames
        if columns is None:
            columns = []
        for needed in ["voter", "deployment_id"]:
            if needed not in columns:
                sys.exit(f"ERROR: missing column '{needed}' in {votes_csv}\n"
                         f"Columns found: {columns}")
        has_platform = "platform" in columns

        for row in reader:
            total_rows += 1
            voter_raw = row["voter"]
            deployment_id = row["deployment_id"]

            # Skip rows with an empty voter or an empty DAO
            if not voter_raw or not deployment_id:
                continue

            formats[detect_format(voter_raw)] += 1
            if has_platform:
                rows_by_platform[row.get("platform", "?")] += 1

            address = extract_address(voter_raw)
            if address not in voter_to_daos:
                voter_to_daos[address] = set()
            voter_to_daos[address].add(deployment_id)

            if total_rows % 2000000 == 0:
                print(f"  ... {total_rows:,} rows processed", flush=True)

    print(f"Rows read in {votes_csv.name}: {total_rows:,}")
    print("  Detected 'voter' formats:")
    for fmt, n in formats.most_common():
        print(f"    - {fmt}: {n:,} rows")
    if rows_by_platform:
        print("  Rows per platform:")
        for platform, n in rows_by_platform.most_common():
            print(f"    - {platform}: {n:,} rows")
    print(f"Unique voters (addresses): {len(voter_to_daos):,}")
    return voter_to_daos


def load_voters(votes_csv, cache_path=VOTERS_CACHE):
    """
    Returns the dictionary {wallet: set(deployment_id)}.

    - If a cache created from THIS same votes.csv exists, it is loaded
      directly (seconds).
    - If it does not exist, or votes.csv has changed since it was created,
      it reads votes.csv (slow, minutes) and saves the result to the cache
      for next time.

    "Same votes.csv" is checked through its size and modification date (the
    "fingerprint"), which are stored inside the cache next to the data.
    """
    file_info = votes_csv.stat()
    fingerprint = {"size": file_info.st_size, "mtime": file_info.st_mtime}

    if cache_path.exists():
        with cache_path.open("rb") as f:
            cache = pickle.load(f)
        if cache["fingerprint"] == fingerprint:
            print(f"Loading voters from cache {cache_path.name} "
                  f"(votes.csv is not read)...", flush=True)
            return cache["voters"]
        print("The cache does not match the current votes.csv: recomputing.",
              flush=True)

    voters = build_voter_to_daos(votes_csv)

    # Save the result for next time
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("wb") as f:
        pickle.dump({"fingerprint": fingerprint, "voters": voters}, f)
    print(f"Cache saved to: {cache_path.resolve()}", flush=True)
    return voters


# ----------------------------------------------------------------------
# 3. Overlap statistics (is the relationship viable?)
# ----------------------------------------------------------------------
def is_excluded(n_daos, max_daos):
    """True if a voter with n_daos DAOs is left out. max_daos = 0 means no limit."""
    if max_daos == 0:
        return False
    return n_daos > max_daos


def get_count(item):
    """Second element of a (name, count) pair. Used to sort by count."""
    return item[1]


def overlap_statistics(voter_to_daos, max_daos):
    # How many voters have exactly 1 DAO, 2 DAOs, 3 DAOs...
    voters_per_n_daos = Counter()
    for daos in voter_to_daos.values():
        voters_per_n_daos[len(daos)] += 1

    multi_dao_voters = 0
    for n_daos, count in voters_per_n_daos.items():
        if n_daos > 1:
            multi_dao_voters += count

    print("\n--- Distribution: number of distinct DAOs per voter ---")
    sorted_values = sorted(voters_per_n_daos)
    for n_daos in sorted_values[:15]:
        print(f"  {n_daos:>4} DAO(s): {voters_per_n_daos[n_daos]:,} voters")
    if len(sorted_values) > 15:
        print("  ... (truncated, there are higher values)")

    total_voters = len(voter_to_daos)
    if total_voters > 0:
        pct = multi_dao_voters / total_voters * 100
    else:
        pct = 0
    print(f"\nVoters who take part in 2+ DAOs: {multi_dao_voters:,} "
          f"of {total_voters:,} ({pct:.2f}%)")

    # "Extreme" voters that exceed the safety threshold
    extremes = []
    for voter, daos in voter_to_daos.items():
        if is_excluded(len(daos), max_daos):
            extremes.append((voter, len(daos)))

    if len(extremes) > 0:
        print(f"\nWarning: {len(extremes)} voters exceed "
              f"the maximum ({max_daos}) of DAOs and will be "
              f"excluded from the edge computation (possible atypical "
              f"bots/delegates). Top 5:")
        extremes.sort(key=get_count, reverse=True)
        for voter, n in extremes[:5]:
            print(f"  {voter}: {n} DAOs")

    return multi_dao_voters


# ----------------------------------------------------------------------
# 4. Build the edges: pairs of DAOs that share voters
# ----------------------------------------------------------------------
def build_edges(voter_to_daos, max_daos):
    """Returns {(dao_a, dao_b): number of shared voters}."""
    weight_by_pair = Counter()
    excluded_voters = 0

    for address, daos in voter_to_daos.items():
        if len(daos) < 2:
            continue  # this voter does not connect anything
        if is_excluded(len(daos), max_daos):
            excluded_voters += 1
            continue

        # Each pair of DAOs this person has voted in adds 1 to that edge.
        # sorted() makes the pair always come in the same order (A, B).
        for dao_a, dao_b in combinations(sorted(daos), 2):
            weight_by_pair[(dao_a, dao_b)] += 1

    if excluded_voters > 0:
        print(f"\n{excluded_voters} voters excluded from the edge "
              f"computation for exceeding the maximum of {max_daos} DAOs.")

    return weight_by_pair


# ----------------------------------------------------------------------
# 5. Summary of the resulting graph
# ----------------------------------------------------------------------
def graph_summary(weight_by_pair):
    if len(weight_by_pair) == 0:
        print("\nNo edge was generated. Check the data.")
        return

    # DAOs that appear in at least one edge
    connected_nodes = set()
    for (dao_a, dao_b) in weight_by_pair:
        connected_nodes.add(dao_a)
        connected_nodes.add(dao_b)

    weights = list(weight_by_pair.values())
    significant = 0
    for weight in weights:
        if weight >= MIN_SIGNIFICANT_WEIGHT:
            significant += 1

    print("\n--- Graph summary (relationship: shared voters) ---")
    print(f"Total number of edges (weight >= 1): {len(weight_by_pair):,}")
    print(f"Number of edges with weight >= {MIN_SIGNIFICANT_WEIGHT}: "
          f"{significant:,}")
    print(f"Number of DAOs connected to at least one other: "
          f"{len(connected_nodes):,}")
    print(f"Minimum / maximum / mean weight: "
          f"{min(weights)} / {max(weights)} / {sum(weights) / len(weights):.2f}")

    print("\nTop 10 DAO pairs with the most shared voters:")
    for (dao_a, dao_b), weight in weight_by_pair.most_common(10):
        print(f"  {dao_a}  <->  {dao_b}   (shared voters: {weight})")


# ----------------------------------------------------------------------
# 6. Save the edges to CSV
# ----------------------------------------------------------------------
def convert_to_team_format(weight_by_pair):
    """
    Converts the edges to the format of the team repository
    (src/edge_generator.py): lowercase DAO ids and each pair sorted
    alphabetically (so A-B and B-A are the same edge).
    Returns {(source, target): shared_voters}.

    If two distinct ids merged when lowercased, it aborts: silently adding
    their edges could count the same voter twice. In the current dataset
    this does not happen (65,752 distinct ids with and without lowercasing).
    """
    converted = {}
    for (dao_a, dao_b), weight in weight_by_pair.items():
        a_lower = dao_a.lower()
        b_lower = dao_b.lower()
        if a_lower <= b_lower:
            key = (a_lower, b_lower)
        else:
            key = (b_lower, a_lower)

        if a_lower == b_lower or key in converted:
            sys.exit("ERROR: two distinct DAO ids coincide when lowercased. "
                     "Check the data before continuing.")
        converted[key] = weight
    return converted


def save_edges(weight_by_pair, output_csv, fmt="original"):
    if fmt == "team":
        header = ["source", "target", "shared_voters"]
        rows = list(convert_to_team_format(weight_by_pair).items())
        # Fixed order so the output is reproducible: first by ids (A to Z),
        # then by weight (highest first). The second sort keeps the order of
        # the first one for edges with the same weight.
        rows.sort()
        rows.sort(key=get_count, reverse=True)
    else:
        header = ["deployment_id_a", "deployment_id_b", "shared_voters_weight"]
        rows = list(weight_by_pair.items())
        rows.sort(key=get_count, reverse=True)

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for (dao_a, dao_b), weight in rows:
            writer.writerow([dao_a, dao_b, weight])
    print(f"\nEdges saved to: {output_csv.resolve()} (format {fmt})")


def parse_arguments():
    """Reads the command-line options (--max-daos, --output and --format)."""
    parser = argparse.ArgumentParser(
        description="Builds the DAO-DAO shared voters graph."
    )
    parser.add_argument(
        "--max-daos",
        type=int,
        default=DEFAULT_MAX_DAOS_PER_VOTER,
        help="Voters who vote in more than N DAOs are excluded. "
             "0 = exclude nobody (baseline without filter). "
             f"Default: {DEFAULT_MAX_DAOS_PER_VOTER}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV. By default it is generated from the threshold: "
             f"{OUTPUT_PREFIX}_max<N>.csv or {OUTPUT_PREFIX}_nolimit.csv "
             "(with --format team: edges_max<N>.csv or edges_nolimit.csv).",
    )
    parser.add_argument(
        "--format",
        choices=["original", "team"],
        default="original",
        help="original: columns deployment_id_a, deployment_id_b, "
             "shared_voters_weight (Sprint 1). team: columns source, "
             "target, shared_voters with lowercase ids, like the team "
             "repository. Default: original.",
    )
    args = parser.parse_args()
    if args.max_daos < 0:
        parser.error("--max-daos must be 0 (no limit) or a positive integer.")
    return args


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    args = parse_arguments()

    # Name of the configuration: "max100", "max50"... or "nolimit"
    max_daos = args.max_daos
    if max_daos > 0:
        label = f"max{max_daos}"
        description = f"{max_daos} DAOs"
    else:
        label = "nolimit"
        description = "no limit (baseline)"

    # Name of the output file
    if args.output:
        output = args.output
    elif args.format == "team":
        output = Path(f"edges_{label}.csv")
    else:
        output = Path(f"{OUTPUT_PREFIX}_{label}.csv")
    print(f"Configuration: maximum DAOs per voter = {description}")
    print(f"Output file: {output} (format {args.format})\n", flush=True)

    if not VOTES_CSV.exists():
        sys.exit(f"ERROR: cannot find {VOTES_CSV}. Adjust the VOTES_CSV path.")

    print("STEP 1/4: getting voters per DAO (cache or votes.csv)...", flush=True)
    voter_to_daos = load_voters(VOTES_CSV)

    print("\nSTEP 2/4: computing overlap statistics...", flush=True)
    overlap_statistics(voter_to_daos, max_daos)

    print("\nSTEP 3/4: building edges (pairs of DAOs)...", flush=True)
    weight_by_pair = build_edges(voter_to_daos, max_daos)

    print("\nSTEP 4/4: generating summary and saving result...", flush=True)
    graph_summary(weight_by_pair)
    save_edges(weight_by_pair, output, args.format)

    print("\n=== PROCESS_COMPLETED_OK ===", flush=True)


if __name__ == "__main__":
    main()
