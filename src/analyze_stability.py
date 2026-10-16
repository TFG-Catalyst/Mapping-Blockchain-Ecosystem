"""
S2-04, step 5: which results are stable and which depend on the threshold.

Key idea. The 4 configurations are nested: the max50 graph is that of the
wallets with <= 50 DAOs; max100 adds the wallets with 51-100; max200 those
with 101-200 and nolimit those with more than 200. That is why the weight of
each edge can be split by "bands" of activity of the wallets that contribute
it:

    weight(nolimit) = weight(max50)                    wallets with   2-50 DAOs
                    + [weight(max100) - weight(max50)]   wallets with  51-100
                    + [weight(max200) - weight(max100)]  wallets with 101-200
                    + [weight(nolimit) - weight(max200)] wallets with >200

It also computes how much of each band comes from the "group" of 469 wallets
of S2-03 (results/S2-03/S2-03_wallets_with_pattern.csv), using the voter
cache.

What it does:
  A. Splits the total weight by bands and measures the group's share in each.
  B. Classifies each edge: stable (its weight does not change with the
     threshold), growing (it exists in all 4 but its weight grows), or
     "new" (it appears when widening).
  C. Hubs: which ones are in the top-N of the 4 configurations and which are
     not, and how much of their weight comes from the group.
  D. Diagnosis: how many edges of each configuration would cease to exist if
     only the 469 wallets of the group were removed, and what part of the
     weight of each configuration belongs to the group.

Usage (from the repository root, where data/raw/votes.csv lives):
  python scripts/analyze_stability.py

Options: --folder (edges and node table of S2-04), --deployments, --group.
Writes to --folder:
  S2-04_stability_bands.csv, S2-04_stability_edges.csv,
  S2-04_stability_hubs.csv, S2-04_stability_vs_no_group.csv
It only reads data; it does not modify anything else.
"""

import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path

import pandas as pd

# We reuse load_voters and the path VOTES_CSV from the first script.
import explore_shared_voters as ev

# Order from lowest to highest threshold: each one contains the previous one.
CONFIGS = ["max50", "max100", "max200", "nolimit"]

# Activity bands of the wallets added by each step: (name, minimum DAOs, maximum DAOs).
BANDS = [
    ("2-50", 2, 50),
    ("51-100", 51, 100),
    ("101-200", 101, 200),
    (">200", 201, 1000000000),
]

# Sizes of the "top N" rankings that are compared.
TOPS = [10, 20, 50, 100]


def band_of(n_daos):
    """Index (0 to 3) of the band a wallet with n_daos DAOs belongs to."""
    for index in range(len(BANDS)):
        name, low, high = BANDS[index]
        if low <= n_daos <= high:
            return index
    return None  # wallets with 0-1 DAOs: they form no edges


# ----------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------
def weight_table(folder, node_ids):
    """One row per edge and one weight column per configuration (0 if it does not exist)."""
    table = None
    for config in CONFIGS:
        edges = pd.read_csv(folder / f"edges_{config}.csv")
        # Same rule as the team's graph_builder: both ends must be known DAOs
        known = edges["source"].isin(node_ids) & edges["target"].isin(node_ids)
        edges = edges[known]
        edges = edges.rename(columns={"shared_voters": f"w_{config}"})
        if table is None:
            table = edges
        else:
            table = table.merge(edges, on=["source", "target"], how="outer")

    weight_columns = []
    for config in CONFIGS:
        weight_columns.append(f"w_{config}")
    table[weight_columns] = table[weight_columns].fillna(0).astype("int64")
    return table


def group_contribution(voter_to_daos, group_wallets):
    """
    For the wallets of the group, counts how much weight each one adds to each
    pair of DAOs, separated by activity band. Returns (list of 4 Counters, wallets found).
    """
    counters = []
    for band in BANDS:
        counters.append(Counter())

    found = 0
    for wallet in group_wallets:
        daos = voter_to_daos.get(wallet)
        if daos is None:
            continue
        found += 1

        # Lowercase ids, same format as the team's CSV
        lowercase_ids = set()
        for dao in daos:
            lowercase_ids.add(dao.lower())
        ids = sorted(lowercase_ids)

        band_index = band_of(len(ids))
        if band_index is None:
            continue
        for pair in combinations(ids, 2):
            counters[band_index][pair] += 1
    return counters, found


def add_group_columns(table, counters):
    """Adds the columns g0..g3 (group weight per band) and g_total to the table."""
    for index in range(len(BANDS)):
        column = f"g{index}"
        if len(counters[index]) > 0:
            pair_rows = []
            for (source, target), weight in counters[index].items():
                pair_rows.append((source, target, weight))
            group_table = pd.DataFrame(pair_rows, columns=["source", "target", column])
            table = table.merge(group_table, on=["source", "target"], how="left")
        else:
            table[column] = 0
        table[column] = table[column].fillna(0).astype("int64")

    group_columns = []
    for index in range(len(BANDS)):
        group_columns.append(f"g{index}")
    table["g_total"] = table[group_columns].sum(axis=1)
    return table


# ----------------------------------------------------------------------
# A. Bands
# ----------------------------------------------------------------------
def step_a_bands(table, folder):
    # Weight of each band per edge = difference between consecutive configurations.
    table["b0"] = table["w_max50"]
    table["b1"] = table["w_max100"] - table["w_max50"]
    table["b2"] = table["w_max200"] - table["w_max100"]
    table["b3"] = table["w_nolimit"] - table["w_max200"]

    # Safety checks
    for index in range(4):
        band_weight = table[f"b{index}"]
        group_weight = table[f"g{index}"]
        assert (band_weight >= 0).all(), "weights are not monotonic: nesting is broken"
        assert (group_weight <= band_weight).all(), (
            f"the group contributes more than band {BANDS[index][0]}: check the attribution")

    total = table["w_nolimit"].sum()
    rows = []
    print("\n===== A. WEIGHT BY WALLET ACTIVITY BAND (nolimit graph) =====")
    print(f"{'band':>8s} {'weight':>12s} {'% of total':>12s} {'edges with weight>0':>20s} {'group weight':>15s} {'% group':>9s}")
    for index in range(len(BANDS)):
        name = BANDS[index][0]
        weight = int(table[f"b{index}"].sum())
        group_weight = int(table[f"g{index}"].sum())
        edges_with_weight = int((table[f"b{index}"] > 0).sum())

        if weight > 0:
            pct_from_group = round(100 * group_weight / weight, 2)
        else:
            pct_from_group = 0

        row = {
            "wallet_dao_band": name,
            "weight": weight,
            "pct_total_weight": round(100 * weight / total, 2),
            "edges_with_band_weight": edges_with_weight,
            "group_weight": group_weight,
            "pct_of_band_from_group": pct_from_group,
        }
        rows.append(row)
        print(f"{name:>8s} {weight:>12,} {row['pct_total_weight']:>11.1f}% "
              f"{edges_with_weight:>20,} {group_weight:>15,} {pct_from_group:>8.1f}%")

    group_total = int(table["g_total"].sum())
    print(f"\n  Total weight (nolimit): {total:,}. "
          f"Share of the group of 469: {group_total:,} ({100 * group_total / total:.1f} %).")
    pd.DataFrame(rows).to_csv(folder / "S2-04_stability_bands.csv", index=False)


# ----------------------------------------------------------------------
# B. Edges
# ----------------------------------------------------------------------
def classify_edges(table):
    """
    Gives each edge a category. The conditions are checked in order and the
    first one that is true wins.
    """
    w50 = table["w_max50"]
    w100 = table["w_max100"]
    w200 = table["w_max200"]
    w_no = table["w_nolimit"]

    conditions = [
        ((w50 > 0) & (w50 == w_no), "1 stable (same weight in all 4)"),
        ((w50 > 0) & (w_no > w50), "2 growing (exists in all 4; weight increases)"),
        ((w50 == 0) & (w100 > 0), "3 new in max100"),
        ((w100 == 0) & (w200 > 0), "4 new in max200"),
        ((w200 == 0) & (w_no > 0), "5 new only in nolimit"),
    ]

    categories = pd.Series("?", index=table.index)
    for condition, label in conditions:
        not_assigned_yet = categories == "?"
        categories[condition & not_assigned_yet] = label

    assert (categories != "?").all(), "some edge has no category"
    return categories


def step_b_edges(table, folder):
    table["category"] = classify_edges(table)
    n_total = len(table)
    w_total = table["w_nolimit"].sum()

    rows = []
    print("\n===== B. EDGE STABILITY =====")
    for category, edges in table.groupby("category"):
        # Edges whose whole weight comes from the group
        all_from_group = int((edges["g_total"] == edges["w_nolimit"]).sum())
        weight = edges["w_nolimit"].sum()
        group_weight = edges["g_total"].sum()
        row = {
            "category": category,
            "edges": len(edges),
            "pct_edges": round(100 * len(edges) / n_total, 2),
            "edges_weight_ge_2": int((edges["w_nolimit"] >= 2).sum()),
            "weight_in_nolimit": int(weight),
            "pct_weight": round(100 * weight / w_total, 2),
            "pct_group_weight": round(100 * group_weight / weight, 2),
            "edges_all_weight_from_group": all_from_group,
        }
        rows.append(row)
    result = pd.DataFrame(rows)
    print(result.to_string(index=False))

    # How much do the growing edges grow?
    growing = table[table["category"].str.startswith("2")]
    ratio = growing["w_nolimit"] / growing["w_max50"]
    print(f"\n  Growing edges: weight in nolimit / weight in max50 -> median ×{ratio.median():.2f}, "
          f"90th percentile ×{ratio.quantile(0.9):.2f}; "
          f"with weight ×2 or more: {(ratio >= 2).sum():,} ({100 * (ratio >= 2).mean():.1f} %).")

    # Edges with weight >= 2 (those with at least 2 shared voters): are they still stable?
    heavy = table[table["w_nolimit"] >= 2]
    print(f"\n  Only edges with weight >= 2 in nolimit ({len(heavy):,}):")
    print(heavy["category"].value_counts().sort_index().to_string())
    result.to_csv(folder / "S2-04_stability_edges.csv", index=False)
    return table


# ----------------------------------------------------------------------
# C. Hubs
# ----------------------------------------------------------------------
def step_c_hubs(table, folder):
    nodes = pd.read_csv(folder / "S2-04_nodes_by_config.csv").set_index("deployment_id")

    # Group weight accumulated in each node (sum over its edges) in nolimit.
    # An edge counts for its source node and for its target node.
    from_source = table.groupby("source")["g_total"].sum()
    from_target = table.groupby("target")["g_total"].sum()
    group_weight_by_node = from_source.add(from_target, fill_value=0)
    group_weight = group_weight_by_node.reindex(nodes.index).fillna(0).astype(int)
    nodes["weighted_degree_group_nolimit"] = group_weight

    # % of the weight of the node that comes from the group (empty if the node has no weight)
    total_weight = nodes["weighted_degree_nolimit"]
    total_weight_no_zeros = total_weight.where(total_weight > 0)
    nodes["pct_group_weight"] = (100 * group_weight / total_weight_no_zeros).round(1)

    print("\n===== C. HUBS: are they in the top-N of the 4 configurations? =====")
    output = []
    for criterion in ["degree", "weighted_degree"]:
        # Position of each node in each configuration (1 = largest value)
        rank_columns = {}
        for config in CONFIGS:
            rank_columns[config] = nodes[f"{criterion}_{config}"].rank(ascending=False, method="first")
        ranks = pd.DataFrame(rank_columns)

        print(f"\n  {criterion}:  N   in all 4 (stable)   in any (union)   only in some")
        for n in TOPS:
            in_top = ranks <= n
            in_all = in_top.all(axis=1)     # in the top N of the 4 configurations
            in_any = in_top.any(axis=1)     # in the top N of at least one
            only_in_some = int(in_any.sum()) - int(in_all.sum())
            print(f"  {' ' * len(criterion)} {n:>4d} {int(in_all.sum()):>14d} "
                  f"{int(in_any.sum()):>18d} {only_in_some:>16d}")

        # We save the nodes of the top 100 of any configuration with their rank in each one.
        in_top100 = ranks <= 100
        selected = in_top100.any(axis=1)
        sub = ranks[selected].astype(int).add_prefix(f"rank_{criterion}_")
        sub["stable_top100"] = in_top100[selected].all(axis=1)
        sub["criterion"] = criterion
        sub = sub.join(nodes[["name", "platform", "pct_group_weight"]])
        output.append(sub.reset_index())

        unstable = sub[sub["stable_top100"] == False]
        stable = sub[sub["stable_top100"] == True]
        print(f"\n  Top 100 by {criterion}: {len(stable)} stable nodes and "
              f"{len(unstable)} that enter or leave depending on the threshold.")
        print(f"  Median % of the node's weight that comes from the group: "
              f"stable {stable['pct_group_weight'].median():.1f} % | "
              f"entering/leaving {unstable['pct_group_weight'].median():.1f} %")

        if criterion == "weighted_degree":
            sample = unstable.sort_values("rank_weighted_degree_nolimit").head(12)
            print("\n  Some that enter/leave (rank by weighted degree):")
            for _, row in sample.iterrows():
                rank_texts = []
                for config in CONFIGS:
                    rank_texts.append(f"{config}:{row[f'rank_{criterion}_{config}']:>5d}")
                print(f"    {str(row['name'])[:26]:26s} {row['platform']:9s} "
                      f"{'  '.join(rank_texts)}   group weight: {row['pct_group_weight']} %")

    pd.concat(output).to_csv(folder / "S2-04_stability_hubs.csv", index=False)


# ----------------------------------------------------------------------
# D. Diagnosis: each configuration versus "removing only the group"
# ----------------------------------------------------------------------
def step_d_no_group(table, folder):
    """
    The group is defined by behavior (S2-03), so "no group" is a diagnosis
    and not a working configuration: it serves to measure how much of each
    configuration depends on those 469 wallets.
    """
    table["w_nogroup"] = table["w_nolimit"] - table["g_total"]
    assert (table["w_nogroup"] >= 0).all()

    exists_without_group = table["w_nogroup"] > 0
    does_not_exist_without_group = table["w_nogroup"] == 0
    print("\n===== D. EACH CONFIGURATION VERSUS REMOVING ONLY THE 469 WALLETS OF THE GROUP =====")
    print(f"  Graph 'nolimit without group': {int(exists_without_group.sum()):,} edges, "
          f"weight {int(table['w_nogroup'].sum()):,}")

    # We go from the least restrictive configuration (nolimit) to the most
    # restrictive one (max50), as in the other tables.
    rows = []
    for k in [3, 2, 1, 0]:
        config = CONFIGS[k]
        in_config = table[f"w_{config}"] > 0
        not_in_config = table[f"w_{config}"] == 0

        # Group weight inside this configuration: only the wallets of the
        # group whose band is included in it count (bands 0 to k).
        group_inside = 0
        for i in range(k + 1):
            group_inside += int(table[f"g{i}"].sum())
        weight_config = int(table[f"w_{config}"].sum())

        n_edges = int(in_config.sum())
        edges_depending_on_group = int((in_config & does_not_exist_without_group).sum())
        edges_missing = int((not_in_config & exists_without_group).sum())
        row = {
            "config": config,
            "edges": n_edges,
            "edges_that_would_not_exist_without_group": edges_depending_on_group,
            "pct_edges_depending_on_group": round(100 * edges_depending_on_group / n_edges, 2),
            "no_group_edges_missing_in_config": edges_missing,
            "total_weight": weight_config,
            "group_weight": group_inside,
            "pct_group_weight": round(100 * group_inside / weight_config, 2),
        }
        rows.append(row)

    result = pd.DataFrame(rows)
    print(result.to_string(index=False))
    result.to_csv(folder / "S2-04_stability_vs_no_group.csv", index=False)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Stability against the threshold (S2-04 step 5).")
    parser.add_argument("--folder", type=Path, default=Path("results/S2-04"))
    parser.add_argument("--deployments", type=Path, default=Path("data/raw/deployments.csv"))
    parser.add_argument("--group", type=Path,
                        default=Path("results/S2-03/S2-03_wallets_with_pattern.csv"))
    return parser.parse_args()


def main():
    args = parse_arguments()

    # Ids of all the known DAOs (lowercase, like the edges files)
    deployments = pd.read_csv(args.deployments, usecols=["deployment_id", "platform", "name"])
    ids = set(deployments["deployment_id"].astype("string").str.lower())

    print("Loading edges of the 4 configurations...", flush=True)
    table = weight_table(args.folder, ids)
    print(f"  {len(table):,} distinct edges in total.", flush=True)

    # Wallets of the group (from S2-03) and the weight they contribute
    group_wallets = pd.read_csv(args.group)["wallet"].str.lower().tolist()
    voter_to_daos = ev.load_voters(ev.VOTES_CSV)
    counters, found = group_contribution(voter_to_daos, group_wallets)
    print(f"  Group wallets found in the cache: {found} of {len(group_wallets)}.", flush=True)
    table = add_group_columns(table, counters)

    step_a_bands(table, args.folder)
    table = step_b_edges(table, args.folder)
    step_c_hubs(table, args.folder)
    step_d_no_group(table, args.folder)
    print(f"\nFiles saved to {args.folder.resolve()}")


if __name__ == "__main__":
    main()
