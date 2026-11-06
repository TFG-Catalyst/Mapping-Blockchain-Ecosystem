"""
S3-06 - Compare the Sprint 2 results (Zenodo v4) with the same analyses rerun on Zenodo v5.

It reads the result files of S2-03, S2-04 and S2-09 from two folders and, for each
metric, says whether the conclusion is STABLE, CHANGED or only SCALES with the data.
It does not compute anything from votes.csv: it only compares result files.

Each folder must contain the subfolders S2-03/, S2-04/ and S2-09/ (the layout of results/).

Verdicts (the tolerances are decisions of the team, kept as constants below):
  STABLE   share within PP_TOL percentage points, or value within REL_TOL (relative),
           or top-k lists overlapping at least OVERLAP_TOL, or same category/flag.
  CHANGED  outside those tolerances.
  SCALE    absolute counts (wallets, edges, weight...). v5 has 5.8 times more votes than
           v4, so these are expected to grow; read their ratio, not stability.
  MISSING  the metric could not be computed (file or column not found).

How to use it (standalone: it needs no repository code, only pandas):
    python compare_v4_v5.py --v4 <repository>/results --v5 <folder with the v5 results> --output-dir <folder>

Self-test: comparing a folder with itself must give no CHANGED and no MISSING.
"""

import argparse
from itertools import combinations
from pathlib import Path

import pandas as pd

REL_TOL = 0.10        # relative change allowed for a value to be STABLE
PP_TOL = 2.0          # percentage points allowed for a share to be STABLE
OVERLAP_TOL = 0.90    # minimum overlap of two top-k lists to be STABLE
TOP_K = 10            # top-k used to compare hub rankings


def to_bool(series):
    """True/False columns written as text or as booleans."""
    return series.astype(str).str.strip().str.lower().eq("true")


class Report:
    def __init__(self):
        self.rows = []

    def add(self, area, metric, v4, v5, kind, note=""):
        self.rows.append({"area": area, "metric": metric, "v4": v4, "v5": v5,
                          "change": change_text(kind, v4, v5),
                          "verdict": verdict(kind, v4, v5), "note": note})

    def missing(self, area, metric, note):
        self.rows.append({"area": area, "metric": metric, "v4": None, "v5": None,
                          "change": "", "verdict": "MISSING", "note": note})


def is_number(x):
    return x is not None and not isinstance(x, (str, bool)) and not pd.isna(x)


def verdict(kind, a, b):
    if kind == "scale":
        return "SCALE"
    if kind == "overlap":                    # a = size of the v4 list, b = how many are still in v5
        return "STABLE" if b / a >= OVERLAP_TOL else "CHANGED"
    if kind in ("same", "bool"):
        return "STABLE" if a == b else "CHANGED"
    if not (is_number(a) and is_number(b)):
        return "MISSING"
    if kind == "share":                      # percentages
        return "STABLE" if abs(b - a) <= PP_TOL else "CHANGED"
    if kind == "rel":
        if a == 0:
            return "STABLE" if b == 0 else "CHANGED"
        return "STABLE" if abs(b - a) / abs(a) <= REL_TOL else "CHANGED"
    raise ValueError(kind)


def change_text(kind, a, b):
    if kind == "overlap":
        return f"{b / a:.0%} overlap"
    if kind in ("same", "bool") or not (is_number(a) and is_number(b)):
        return ""
    if kind == "share":
        return f"{b - a:+.2f} pp"
    if a == 0:
        return "" if b == 0 else "new"
    return f"x{b / a:.2f}"


def read(root, area, name):
    path = Path(root) / area / name
    return pd.read_csv(path) if path.exists() else None


def both(report, area, name, fn, v4_root, v5_root):
    """Read the same file from both folders and run fn(report, df4, df5)."""
    d4, d5 = read(v4_root, area, name), read(v5_root, area, name)
    if d4 is None or d5 is None:
        report.missing(area, name, "file not found in " + ("v4" if d4 is None else "v5"))
        return
    try:
        fn(report, d4, d5)
    except KeyError as error:
        report.missing(area, name, f"column not found: {error}")


# ---------------------------------------------------------------- S2-03
def percentile(freq, q):
    freq = freq.sort_values("n_daos")
    cum = freq["voters"].cumsum()
    return int(freq.loc[cum >= q / 100 * cum.iloc[-1], "n_daos"].iloc[0])


def activity(report, f4, f5):
    def stats(f):
        total = f["voters"].sum()
        return {"total": total, "single": f.loc[f["n_daos"] == 1, "voters"].sum() / total * 100,
                "over100": f.loc[f["n_daos"] > 100, "voters"].sum(),
                "over200": f.loc[f["n_daos"] > 200, "voters"].sum(), "max": f["n_daos"].max()}
    s4, s5 = stats(f4), stats(f5)
    a = "S2-03"
    report.add(a, "wallets in votes.csv", s4["total"], s5["total"], "scale")
    report.add(a, "% of wallets voting in one DAO", s4["single"], s5["single"], "share")
    for q in (50, 90, 99, 99.9):
        report.add(a, f"p{q:g} of DAOs per wallet", percentile(f4, q), percentile(f5, q), "rel")
    report.add(a, "maximum DAOs of one wallet", s4["max"], s5["max"], "rel")
    report.add(a, "wallets with more than 100 DAOs", s4["over100"], s5["over100"], "scale")
    report.add(a, "% of wallets with more than 100 DAOs", s4["over100"] / s4["total"] * 100,
               s5["over100"] / s5["total"] * 100, "rel")
    report.add(a, "wallets with more than 200 DAOs", s4["over200"], s5["over200"], "scale")


def threshold_order(label):
    """'no limit' first, then the numeric thresholds from high to low."""
    return (0, 0) if not label.isdigit() else (1, -int(label))


def threshold_name(label):
    return f"max{label}" if label.isdigit() else label


def thresholds(report, t4, t5):
    a = "S2-03"
    t4["threshold"], t5["threshold"] = t4["threshold"].astype(str), t5["threshold"].astype(str)
    for t in sorted(set(t4["threshold"]) & set(t5["threshold"]), key=threshold_order):
        r4 = t4[t4["threshold"] == t].iloc[0]
        r5 = t5[t5["threshold"] == t].iloc[0]
        name = threshold_name(t)
        report.add(a, f"{name}: wallets excluded", r4["excluded_wallets"], r5["excluded_wallets"], "scale")
        report.add(a, f"{name}: excluded wallets NOT in the group", r4["excluded_others"],
                   r5["excluded_others"], "rel")
        report.add(a, f"{name}: % of graph weight from the group", r4["pct_group_weight"],
                   r5["pct_group_weight"], "share")
    # The reason max100 was chosen in Sprint 2: it removes only wallets of the group.
    if "100" in set(t4["threshold"]) and "100" in set(t5["threshold"]):
        z4 = t4.loc[t4["threshold"] == "100", "excluded_others"].iloc[0] == 0
        z5 = t5.loc[t5["threshold"] == "100", "excluded_others"].iloc[0] == 0
        report.add(a, "max100 excludes only wallets of the group", z4, z5, "bool",
                   "decision criterion of S2-04")
    else:
        report.missing(a, "max100 excludes only wallets of the group", "threshold 100 not found")


def group(report, g4, g5):
    s4, s5 = set(g4["wallet"].str.lower()), set(g5["wallet"].str.lower())
    report.add("S2-03", "wallets that follow the pattern (group)", len(s4), len(s5), "rel")
    report.add("S2-03", "v4 group wallets still in the v5 group", len(s4), len(s4 & s5), "overlap")


# ---------------------------------------------------------------- S2-04
def metrics(report, m4, m5):
    a = "S2-04"
    m4, m5 = m4.set_index("config"), m5.set_index("config")
    for config in [c for c in m4.index if c in m5.index]:
        for col, kind in [("edges", "scale"), ("total_weight", "scale"), ("isolated_nodes", "scale"),
                          ("components", "scale"), ("largest_component", "scale"),
                          ("pct_edges_weight_ge_2", "share"), ("mean_degree", "rel"),
                          ("median_weight", "rel")]:
            report.add(a, f"{config}: {col}", m4.loc[config, col], m5.loc[config, col], kind)
    if {"max200", "max100", "nolimit"} <= set(m4.index) & set(m5.index):
        def shape(m):
            return ((m.loc["max200", "edges"] - m.loc["max100", "edges"]) / m.loc["max200", "edges"] * 100,
                    m.loc["max100", "total_weight"] / m.loc["nolimit", "total_weight"] * 100)
        (e4, w4), (e5, w5) = shape(m4), shape(m5)
        report.add(a, "% of edges lost from max200 to max100", e4, e5, "share")
        report.add(a, "max100 weight as % of nolimit weight", w4, w5, "share")


def no_group(report, n4, n5):
    n4, n5 = n4.set_index("config"), n5.set_index("config")
    for config in [c for c in n4.index if c in n5.index]:
        report.add("S2-04", f"{config}: % of weight from the group", n4.loc[config, "pct_group_weight"],
                   n5.loc[config, "pct_group_weight"], "share")
        report.add("S2-04", f"{config}: % of edges that depend on the group",
                   n4.loc[config, "pct_edges_depending_on_group"],
                   n5.loc[config, "pct_edges_depending_on_group"], "share")


def bands(report, b4, b5):
    b4, b5 = b4.set_index("wallet_dao_band"), b5.set_index("wallet_dao_band")
    for band in [b for b in b4.index if b in b5.index]:
        report.add("S2-04", f"weight share of wallets with {band} DAOs", b4.loc[band, "pct_total_weight"],
                   b5.loc[band, "pct_total_weight"], "share")


def top_sets(df, k):
    """{(criterion, config): set of the top-k deployment_id}."""
    top = df[df["position"] <= k]
    return {key: set(g["deployment_id"]) for key, g in top.groupby(["criterion", "config"])}


def hubs(report, h4, h5):
    s4, s5 = top_sets(h4, TOP_K), top_sets(h5, TOP_K)
    for key in sorted(set(s4) & set(s5)):
        report.add("S2-04", f"top {TOP_K} by {key[0]} ({key[1]}): v4 hubs still in v5", len(s4[key]),
                   len(s4[key] & s5[key]), "overlap")
    for name, sets in (("v4", s4), ("v5", s5)):
        for criterion in sorted({k[0] for k in sets}):
            same = len({frozenset(v) for k, v in sets.items() if k[0] == criterion}) == 1
            report.rows.append({"area": "S2-04", "metric": f"top {TOP_K} by {criterion} is the same in all "
                                f"configurations ({name})", "v4": None, "v5": same, "change": "",
                                "verdict": "INFO", "note": ""})


def stability_hubs(report, s4, s5):
    for criterion in sorted(set(s4["criterion"]) & set(s5["criterion"])):
        shares = []
        for df in (s4, s5):
            part = df[df["criterion"] == criterion]
            shares.append(to_bool(part["stable_top100"]).mean() * 100)
        report.add("S2-04", f"% of top-100 hubs by {criterion} stable across thresholds", *shares, "share")


# ---------------------------------------------------------------- S2-09
# The category of each selected hub is assigned by hand in select_hubs.py (SELECTION), so
# rerunning it always gives the same categories. What can change with new data is whether the
# flags of classify_hubs.py still support each category.
CATEGORY_FLAG = {"filter-dependent": "F_filter", "proportional-overlap cluster": "F_overlap",
                 "same-organization cluster": "F_org", "dominated by community size": "F_size"}
FLAGS = ["F_filter", "F_overlap", "F_size", "F_org"]


def unsupported(selected_df, indicators_df):
    """Selected hubs whose category is not backed by the flags: [(name, category, flags that are on)]."""
    ind = indicators_df.set_index("deployment_id")
    bad = []
    for _, hub in selected_df.iterrows():
        if hub["deployment_id"] not in ind.index:
            bad.append((hub["name"], hub["category"], "not in the indicators table"))
            continue
        on = [f for f in FLAGS if to_bool(pd.Series([ind.loc[hub["deployment_id"], f]])).iloc[0]]
        needed = CATEGORY_FLAG.get(hub["category"])
        backed = (needed in on) if needed else (len(on) == 0)     # "stable" = no flag at all
        if not backed:
            bad.append((hub["name"], hub["category"], ", ".join(on) or "no flag"))
    return bad


def categories(report, v4_root, v5_root, details):
    names = ("S2-09_selected_hubs.csv", "S2-09_hub_indicators.csv")
    d4 = [read(v4_root, "S2-09", n) for n in names]
    d5 = [read(v5_root, "S2-09", n) for n in names]
    if any(d is None for d in d4 + d5):
        report.missing("S2-09", "category of each selected hub backed by the flags", "files not found")
        return
    b4, b5 = unsupported(*d4), unsupported(*d5)
    report.add("S2-09", "selected hubs found whose category is backed by the flags",
               len(d4[0]) - len(b4), len(d5[0]) - len(b5), "same",
               "category = hand-assigned; flags = F_filter/F_overlap/F_size/F_org")
    report.add("S2-09", "selected hubs found whose category is NOT backed by the flags", len(b4), len(b5), "same")
    details["unsupported_v4"], details["unsupported_v5"] = b4, b5


def selected(report, s4, s5):
    s4, s5 = s4.set_index("deployment_id"), s5.set_index("deployment_id")
    common = [d for d in s4.index if d in s5.index]
    neighbor = sum(s4.loc[d, "neighbor_1"] == s5.loc[d, "neighbor_1"] for d in common)
    report.add("S2-09", "selected hubs (of the v4 selection) found in v5", len(s4), len(common), "same")
    report.add("S2-09", "selected hubs with the same main neighbour", len(common), neighbor, "same")


def indicators(report, i4, i5):
    i4, i5 = i4.set_index("deployment_id"), i5.set_index("deployment_id")
    common = [d for d in i4.index if d in i5.index]
    report.add("S2-09", "nodes in the indicators table", len(i4), len(i5), "rel")
    for flag in ("F_filter", "F_overlap", "F_size", "F_org"):
        # whole tables (the candidate set is different in v4 and v5)
        w4, w5 = int(to_bool(i4[flag]).sum()), int(to_bool(i5[flag]).sum())
        report.add("S2-09", f"{flag}: nodes with the flag (whole table)", w4, w5, "rel")
        # only nodes that are in both tables
        f4, f5 = to_bool(i4.loc[common, flag]), to_bool(i5.loc[common, flag])
        report.add("S2-09", f"{flag}: nodes in both tables with the flag", int(f4.sum()), int(f5.sum()), "rel")
        report.add("S2-09", f"{flag}: nodes in both tables where the flag changed", 0, int((f4 != f5).sum()), "same")


def candidates(report, c4, c5, details):
    s4, s5 = set(c4["deployment_id"]), set(c5["deployment_id"])
    report.add("S2-09", "v4 hub candidates still candidates in v5", len(s4), len(s4 & s5), "overlap")
    new = c5[c5["deployment_id"].isin(s5 - s4)]
    details["new_candidates"] = list(zip(new["name"], new["platform"], new["deployment_id"]))


# ---------------------------------------------------------------- output
def fmt(x):
    if x is None or (not isinstance(x, (str, bool)) and pd.isna(x)):
        return ""
    if isinstance(x, (bool, str)):
        return str(x)
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.3f}"


def write_markdown(report, details, path):
    lines = ["# S3-06 - Stable and changed results (v4 vs v5)", "",
             f"Tolerances: share +-{PP_TOL} pp, value +-{REL_TOL:.0%}, top-{TOP_K} overlap >= {OVERLAP_TOL:.0%}. "
             "SCALE = absolute count that grows with the data.", ""]
    for area in ("S2-03", "S2-04", "S2-09"):
        rows = [r for r in report.rows if r["area"] == area]
        lines += [f"## {area}", "", "| Metric | v4 | v5 | Change | Verdict |", "| --- | ---: | ---: | ---: | :--- |"]
        lines += [f"| {r['metric']} | {fmt(r['v4'])} | {fmt(r['v5'])} | {r['change']} | {r['verdict']} |" for r in rows]
        lines.append("")
    for key, title in (("unsupported_v4", "v4"), ("unsupported_v5", "v5")):
        if details.get(key):
            lines += [f"## Selected hubs whose category is not backed by the flags ({title})", "",
                      "| Hub | Category | Flags that are on |", "| --- | --- | --- |"]
            lines += [f"| {n} | {c} | {f} |" for n, c, f in details[key]] + [""]
    if details.get("new_candidates"):
        lines += ["## New hub candidates in v5 (identity NOT verified)", "", "| Name | Platform | deployment_id |",
                  "| --- | --- | --- |"]
        lines += [f"| {n} | {p} | {d} |" for n, p, d in details["new_candidates"]] + [""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v4", type=Path, required=True, help="results folder of Sprint 2 (v4)")
    parser.add_argument("--v5", type=Path, required=True, help="results folder of the rerun on v5")
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    report, details = Report(), {}
    a, b = args.v4, args.v5
    both(report, "S2-03", "S2-03_frequency_by_n_daos.csv", activity, a, b)
    both(report, "S2-03", "S2-03_threshold_comparison.csv", thresholds, a, b)
    both(report, "S2-03", "S2-03_wallets_with_pattern.csv", group, a, b)
    both(report, "S2-04", "S2-04_metrics_by_config.csv", metrics, a, b)
    both(report, "S2-04", "S2-04_stability_vs_no_group.csv", no_group, a, b)
    both(report, "S2-04", "S2-04_stability_bands.csv", bands, a, b)
    both(report, "S2-04", "S2-04_hubs_by_config.csv", hubs, a, b)
    both(report, "S2-04", "S2-04_stability_hubs.csv", stability_hubs, a, b)
    both(report, "S2-09", "S2-09_selected_hubs.csv", selected, a, b)
    categories(report, a, b, details)
    both(report, "S2-09", "S2-09_hub_indicators.csv", indicators, a, b)
    both(report, "S2-09", "S2-09_hub_candidates.csv", lambda r, x, y: candidates(r, x, y, details), a, b)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(report.rows)
    table.to_csv(args.output_dir / "S3-06_v4_vs_v5.csv", index=False)
    write_markdown(report, details, args.output_dir / "S3-06_v4_vs_v5.md")
    print(table["verdict"].value_counts().to_string())
    print(f"Written to {args.output_dir}/S3-06_v4_vs_v5.csv and .md")


if __name__ == "__main__":
    main()
