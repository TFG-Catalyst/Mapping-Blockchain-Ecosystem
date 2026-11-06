"""
S3-06: overlap between a hub and its main neighbours, with the sizes of the communities
counted from votes.csv (not from deployments.csv).

Why: classify_hubs.py (S2-09) divides the shared voters of an edge by `unique_voters` of
deployments.csv. The data dictionary says that this counter describes a different
population from votes.csv and must not be combined with measures computed from votes.csv
(the same rule agreed for Jaccard). With v5 the problem is visible: `unique_voters` is 0 for
some of the new hubs and the "proportion" is above 1 for others.

What it does, for the candidates of results/S2-09/S2-09_hub_indicators.csv (and the selected
hubs that are no longer candidates):
  - size of every community = distinct wallets that voted in the DAO, among the wallets that
    the graph keeps (at most --max-daos DAOs, 100 by default), single-DAO voters included
    (as the denominator of Jaccard in S2-05/06),
  - shared voters = weight of the edge in the max100 graph (same filter as the sizes),
  - overlap coefficient = shared / smaller community, Jaccard = shared / (A + B - shared),
  - F_overlap and F_size recomputed with the same thresholds as classify_hubs.py, to compare
    them with the flags computed from deployments.csv.

Reads: data/raw/votes.csv (through the voter cache of explore_shared_voters.py),
results/S2-04/edges_max100.csv, S2-04_nodes_by_config.csv, S2-04_stability_hubs.csv and
S2-09/S2-09_hub_indicators.csv. Writes two CSV files in results/S2-09/.

Usage (from the working folder of S3-06, with PYTHONPATH = repository):
  python <repo>/analysis/s3_06_v5_comparison/recompute_overlap_v5.py
"""
import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from analysis.common.explore_shared_voters import load_voters
from analysis.s2_09_ecosystem_hubs.classify_hubs import DEGREE_GAP, OVERLAP_THRESHOLD, TOP_SIZE


def community_sizes(voters, max_daos):
    """{deployment_id (lowercase): wallets that voted in it} among wallets with <= max_daos DAOs."""
    sizes = Counter()
    for daos in voters.values():
        if max_daos and len(daos) > max_daos:
            continue
        for dao in daos:
            sizes[dao.lower()] += 1
    return sizes


def main_neighbours(edges, nodes, top=5):
    """Long table (hub, neighbour, shared_voters) with the `top` strongest neighbours of each hub."""
    both = pd.concat([
        edges.rename(columns={"source": "hub", "target": "neighbour"}),
        edges.rename(columns={"target": "hub", "source": "neighbour"}),
    ])
    both = both[both["hub"].isin(nodes)]
    both = both.sort_values(["hub", "shared_voters", "neighbour"], ascending=[True, False, True])
    return both.groupby("hub").head(top)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max-daos", type=int, default=100)
    parser.add_argument("--votes", type=Path, default=Path("data/raw/votes.csv"))
    parser.add_argument("--cache", type=Path, default=Path("data/processed/voters_cache.pkl"))
    parser.add_argument("--trust-cache", action="store_true",
                        help="load the cache without comparing it with votes.csv (votes.csv is not needed)")
    parser.add_argument("--s204", type=Path, default=Path("results/S2-04"))
    parser.add_argument("--s209", type=Path, default=Path("results/S2-09"))
    args = parser.parse_args()

    indicators = pd.read_csv(args.s209 / "S2-09_hub_indicators.csv").set_index("deployment_id")
    nodes = pd.read_csv(args.s204 / "S2-04_nodes_by_config.csv").set_index("deployment_id")
    nodes.index = nodes.index.str.lower()
    names = nodes["name"]
    edges = pd.read_csv(args.s204 / f"edges_max{args.max_daos}.csv")

    # Hubs: the candidates of S2-09 plus the selected hubs that are not candidates any more
    hubs = set(indicators.index)
    lost = args.s209 / "S2-09_selected_hubs_not_found.csv"
    extra = {}
    if lost.exists():
        stability = pd.read_csv(args.s204 / "S2-04_stability_hubs.csv")
        stability = stability[stability["criterion"] == "weighted_degree"]
        for _, row in pd.read_csv(lost).iterrows():
            found = stability[(stability["name"] == row["name"]) & (stability["platform"] == row["platform"])]
            if len(found) == 1:
                extra[found.iloc[0]["deployment_id"]] = row["rank_weighted_max100"]
                hubs.add(found.iloc[0]["deployment_id"])

    print("Loading voters (cache)...", flush=True)
    if args.trust_cache:
        import pickle
        with args.cache.open("rb") as f:
            voters = pickle.load(f)["voters"]
    else:
        voters = load_voters(args.votes, args.cache)
    sizes = community_sizes(voters, args.max_daos)
    sizes_all = community_sizes(voters, 0)
    print(f"Communities: {len(sizes):,} deployments with voters; wallets: {len(voters):,}")

    # Rank by community size among all deployments (as rank_unique_voters, but from votes.csv)
    ordered = sorted(sizes, key=lambda d: (-sizes[d], d))
    size_rank = {d: i + 1 for i, d in enumerate(ordered)}

    near = main_neighbours(edges, hubs)
    pairs = []
    for _, row in near.iterrows():
        hub, neighbour, shared = row["hub"], row["neighbour"], int(row["shared_voters"])
        a, b = sizes.get(hub, 0), sizes.get(neighbour, 0)
        smaller = min(a, b)
        pairs.append({
            "hub": hub, "hub_name": names.get(hub), "neighbour": neighbour,
            "neighbour_name": names.get(neighbour), "shared_voters": shared,
            "voters_hub": a, "voters_neighbour": b,
            "overlap_coefficient": round(shared / smaller, 3) if smaller else None,
            "jaccard": round(shared / (a + b - shared), 3) if (a + b - shared) else None,
        })
    pairs = pd.DataFrame(pairs)
    pairs["position"] = pairs.groupby("hub").cumcount() + 1
    pairs.to_csv(args.s209 / "S3-06_overlap_from_votes.csv", index=False)

    flags = []
    for hub in sorted(hubs):
        first = pairs[(pairs["hub"] == hub) & (pairs["position"] == 1)]
        first = first.iloc[0] if len(first) else None
        in_table = hub in indicators.index
        overlap = None if first is None else first["overlap_coefficient"]
        overlap = None if overlap is None or pd.isna(overlap) else round(float(overlap), 2)
        if in_table:
            gap = int(indicators.at[hub, "rank_degree_max100"] - indicators.at[hub, "rank_weighted_max100"])
        else:
            gap = None
        flag_overlap = bool(overlap is not None and overlap >= OVERLAP_THRESHOLD and gap is not None and gap >= DEGREE_GAP)
        rank = size_rank.get(hub)
        flags.append({
            "deployment_id": hub, "name": names.get(hub),
            "in_indicators_table": in_table,
            "unique_voters_deployments_csv": indicators.at[hub, "unique_voters"] if in_table else None,
            "voters_votes_csv_max100": sizes.get(hub, 0),
            "voters_votes_csv_all": sizes_all.get(hub, 0),
            "rank_by_voters_votes_csv": rank,
            "neighbour_1_old": indicators.at[hub, "neighbor_1"] if in_table else None,
            "neighbour_1_new": None if first is None else first["neighbour_name"],
            "proportion_old": indicators.at[hub, "neighbor_1_proportion"] if in_table else None,
            "overlap_coefficient_new": overlap,
            "jaccard_new": None if first is None else first["jaccard"],
            "F_overlap_old": bool(indicators.at[hub, "F_overlap"]) if in_table else None,
            "F_overlap_new": flag_overlap if in_table else None,
            "F_size_old": bool(indicators.at[hub, "F_size"]) if in_table else None,
            "F_size_new": bool(rank is not None and rank <= TOP_SIZE) if in_table else None,
        })
    flags = pd.DataFrame(flags).sort_values("voters_votes_csv_max100", ascending=False)
    flags.to_csv(args.s209 / "S3-06_hub_flags_from_votes.csv", index=False)

    table = flags[flags["in_indicators_table"]]
    print("\nF_overlap: old", int(table["F_overlap_old"].sum()), "-> new", int(table["F_overlap_new"].sum()),
          "| changed:", int((table["F_overlap_old"] != table["F_overlap_new"]).sum()))
    print("F_size   : old", int(table["F_size_old"].sum()), "-> new", int(table["F_size_new"].sum()),
          "| changed:", int((table["F_size_old"] != table["F_size_new"]).sum()))
    print("Proportion above 1 in the old table:", int((pd.to_numeric(table["proportion_old"]) > 1).sum()),
          "| overlap coefficient above 1 now:", int((pd.to_numeric(table["overlap_coefficient_new"]) > 1).sum()))
    print(f"\nWritten: {args.s209 / 'S3-06_overlap_from_votes.csv'} and {args.s209 / 'S3-06_hub_flags_from_votes.csv'}")


if __name__ == "__main__":
    main()
