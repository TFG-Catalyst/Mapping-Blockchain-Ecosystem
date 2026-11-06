"""
S3-06: runs the select_hubs.py of the repository on the v5 indicators, tolerating the
selected hubs that are no longer candidates.

select_hubs.py aborts if a hub of its hand-written SELECTION is not found exactly once in
S2-09_hub_indicators.csv. With v5 some of them are not among the candidates (top 60 by
weighted degree in any configuration) any more. That is a RESULT, not an error, so here:
  - the repository module is imported and its SELECTION is kept as it is,
  - the hubs that are not in the indicators are taken out of the list only for this run,
  - they are written to results/S2-09/S2-09_selected_hubs_not_found.csv with their ranks
    and group weight in the S2-04 graphs, so the information is not lost.
The repository is not modified.

Run from the working folder of S3-06 (see docs/S3-06_filter_and_hubs_on_v5.md) with PYTHONPATH = repository.
"""
import pandas as pd
from analysis.s2_09_ecosystem_hubs import select_hubs as sh

indicators = pd.read_csv(sh.INDICATORS)
present, absent = [], []
for entry in sh.SELECTION:
    name, platform = entry[0], entry[1]
    n = len(indicators[(indicators["name"] == name) & (indicators["platform"] == platform)])
    (present if n == 1 else absent).append(entry)

print(f"{len(present)} of {len(sh.SELECTION)} selected hubs are in the v5 indicators")
if absent:
    stab = pd.read_csv("results/S2-04/S2-04_stability_hubs.csv")
    stab = stab[stab["criterion"] == "weighted_degree"]
    rows = []
    for name, platform, category, _ in absent:
        s = stab[(stab["name"] == name) & (stab["platform"] == platform)]
        row = {"category_v4": category, "name": name, "platform": platform}
        if len(s) == 1:
            s = s.iloc[0]
            for c in ["nolimit", "max200", "max100", "max50"]:
                row["rank_weighted_" + c] = s["rank_weighted_degree_" + c]
            row["pct_group_weight_nolimit"] = s["pct_group_weight"]
        rows.append(row)
        print(f"  NOT a candidate in v5: {name}/{platform} ({category})")
    pd.DataFrame(rows).to_csv("results/S2-09/S2-09_selected_hubs_not_found.csv", index=False)
    print("  written results/S2-09/S2-09_selected_hubs_not_found.csv")

sh.SELECTION = present
sh.main()
