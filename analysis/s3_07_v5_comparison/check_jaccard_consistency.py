"""
S3-07 - Second check of the Jaccard weights: are numerators and denominators consistent?

For every edge of edges_jaccard.csv the rules below must hold (the pipeline checks them too while
it runs; this repeats them on the saved file). Result: results/S3-07/S2-06/S3-07_jaccard_consistency.txt

Run from the project root:  python -m analysis.s3_07_v5_comparison.check_jaccard_consistency
"""

import pandas as pd

from src.paths import PROCESSED_DATA_DIR, RESULTS_DIR

jaccard = pd.read_csv(PROCESSED_DATA_DIR / "edges_jaccard.csv")
edges = pd.read_csv(PROCESSED_DATA_DIR / "edges.csv")
sizes = jaccard[["voters_source", "voters_target"]]       # voters of the two DAOs of each edge
both = jaccard.merge(edges, on=["source", "target"], suffixes=("_jaccard", "_edges"))

# Each rule is True for the edges that follow it
rules = {
    "union = voters_source + voters_target - shared": jaccard["union_voters"] == sizes.sum(axis=1) - jaccard["shared_voters"],
    "shared <= smaller DAO": jaccard["shared_voters"] <= sizes.min(axis=1),
    "union >= bigger DAO": jaccard["union_voters"] >= sizes.max(axis=1),
    "jaccard = shared / union": (jaccard["jaccard"] - jaccard["shared_voters"] / jaccard["union_voters"]).abs() < 1e-9,
    "0 < jaccard <= 1": (jaccard["jaccard"] > 0) & (jaccard["jaccard"] <= 1),
}

lines = [f"Edges in edges_jaccard.csv: {len(jaccard):,} | in edges.csv: {len(edges):,}"]
for rule, follows in rules.items():
    lines.append(f"{'OK  ' if follows.all() else 'FAIL'} {rule}: {(~follows).sum():,} edges break it")
same = len(both) == len(jaccard) == len(edges) and (both["shared_voters_jaccard"] == both["shared_voters_edges"]).all()
lines.append(f"{'OK  ' if same else 'FAIL'} same pairs and same shared voters as edges.csv")

print("\n".join(lines))
(RESULTS_DIR / "S3-07" / "S2-06" / "S3-07_jaccard_consistency.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
