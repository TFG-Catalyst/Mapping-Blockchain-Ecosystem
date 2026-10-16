"""
S2-09, step 4: hub selection and classification.

Reads results/S2-09/S2-09_hub_indicators.csv (output of classify_hubs.py) and
results/S2-09/S2-09_verified_identity.csv, and writes
results/S2-09/S2-09_selected_hubs.csv with the chosen hubs, their category
and a brief interpretation.

The only manual part is the SELECTION list (category and interpretation of
each hub). All the figures come from the CSVs, they are not typed by hand.
The selection and the categories are PROVISIONAL until the normalized
results of S2-05/06 are available (column normalized_measure_S2_05_06,
empty for now).

Usage (from the repository root):
  python scripts/select_hubs.py

It only reads files; the only thing it writes is the output CSV.
"""

import sys
from pathlib import Path

import pandas as pd

FOLDER = Path("results/S2-09")
INDICATORS = FOLDER / "S2-09_hub_indicators.csv"
IDENTITY = FOLDER / "S2-09_verified_identity.csv"
OUTPUT = FOLDER / "S2-09_selected_hubs.csv"

# The five categories
SIZE = "dominated by community size"
FILTER = "filter-dependent"
ORG = "same-organization cluster"
OVERLAP = "proportional-overlap cluster"
STABLE = "stable"

# Texts that are repeated for several hubs
TEXT_SIZE = ("Among the nodes with the most unique voters; its weight is consistent "
             "with the size of its community. Stable position in the 4 configurations.")
TEXT_BALSAM_TARPON = ("It shares almost all the voters of the smaller of the two with its "
                      "main neighbor ({other}) and does not depend on the filter. The cause "
                      "is unknown; the exact proportion will be given by S2-05/06. "
                      "Unverified and without a description.")
TEXT_ARBITRUM = ("Its main neighbor is the other Arbitrum governor (same implementation, "
                 "verified on Arbiscan): the strongest link is internal to the organization.")
TEXT_STABLE = ("No flag: its rank by weighted degree is better than by unique voters and "
               "does not change between configurations.")

# One element per selected hub: (name, platform, category, interpretation)
SELECTION = [
    ("Metrox", "snapshot", FILTER,
     "Almost all of its weight comes from the wallets of the group: without them it loses "
     "its hub position. Unverified space, described on Snapshot as 'Metrox test space'."),
    ("Strio", "snapshot", FILTER,
     "Almost all of its weight comes from the wallets of the group. Its id is "
     "test6.shot.eth, unverified and without a description."),
    ("balsam", "snapshot", OVERLAP, TEXT_BALSAM_TARPON.format(other="tarpon")),
    ("tarpon", "snapshot", OVERLAP, TEXT_BALSAM_TARPON.format(other="balsam")),
    ("arbitrum treasury", "tally", ORG, TEXT_ARBITRUM),
    ("arbitrum core", "tally", ORG, TEXT_ARBITRUM),
    ("Uniswap", "snapshot", ORG,
     "Its main neighbor is the Uniswap governor on Tally: the strongest link is internal "
     "to the organization."),
    ("uniswap", "tally", ORG,
     "Its main neighbor is the Uniswap space on Snapshot: the strongest link is internal "
     "to the organization."),
    ("PancakeSwap", "snapshot", SIZE, TEXT_SIZE),
    ("Aave DAO", "snapshot", SIZE, TEXT_SIZE),
    ("Stargate DAO", "snapshot", SIZE, TEXT_SIZE),
    ("Lido", "snapshot", STABLE, TEXT_STABLE),
    ("ENS", "snapshot", STABLE, TEXT_STABLE),
    ("test", "tally", SIZE,
     "It is not a test DAO: it is Optimism Governance (Agora), verified on Optimistic "
     "Etherscan. Among the 5 nodes with the most unique voters."),
    ("OpenDAO", "snapshot", SIZE,
     "Borderline case (30th by unique voters). Its own weight is the same in nolimit, "
     "max200 and max100: the change in rank is relative, due to the nodes that the group "
     "inflates ahead of it."),
]


def main():
    for path in [INDICATORS, IDENTITY]:
        if not path.exists():
            sys.exit(f"ERROR: {path} does not exist")
    indicators = pd.read_csv(INDICATORS)
    identity = pd.read_csv(IDENTITY).set_index("deployment_id")["verified_label"]

    rows = []
    for name, platform, category, interpretation in SELECTION:
        # Look for the hub in the indicators table (it must appear exactly once)
        found = indicators[(indicators["name"] == name) & (indicators["platform"] == platform)]
        if len(found) != 1:
            sys.exit(f"ERROR: {name}/{platform} appears {len(found)} times in the indicators")
        hub = found.iloc[0]

        rows.append({
            "category": category,
            "name": name,
            "platform": platform,
            "deployment_id": hub["deployment_id"],
            "verified_identity": identity.get(hub["deployment_id"], ""),
            "rank_weighted_nolimit": hub["rank_weighted_nolimit"],
            "rank_weighted_max200": hub["rank_weighted_max200"],
            "rank_weighted_max100": hub["rank_weighted_max100"],
            "rank_weighted_max50": hub["rank_weighted_max50"],
            "pct_group_weight_nolimit": hub["pct_group_weight_nolimit"],
            "unique_voters": hub["unique_voters"],
            "rank_unique_voters": hub["rank_unique_voters"],
            "neighbor_1": hub["neighbor_1"],
            "neighbor_1_weight": hub["neighbor_1_weight"],
            "neighbor_1_proportion": hub["neighbor_1_proportion"],
            "interpretation": interpretation,
            "normalized_measure_S2_05_06": "",
        })

    result = pd.DataFrame(rows)

    # Hubs whose identity has not been verified yet
    without_identity = []
    for index in range(len(result)):
        if result.at[index, "verified_identity"] == "":
            without_identity.append(result.at[index, "name"])

    result.to_csv(OUTPUT, index=False)
    print(f"{len(result)} hubs written to {OUTPUT}")
    print(result["category"].value_counts().to_string())
    if len(without_identity) > 0:
        print("Without verified identity:", without_identity)
    else:
        print("Without verified identity: none")


if __name__ == "__main__":
    main()
