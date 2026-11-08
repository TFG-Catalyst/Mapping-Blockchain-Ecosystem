"""
S3-08 - Descriptive tables, generated from code (CSV files in results/S3-08/).

    1. Rows per file and platform        2. Coverage of the votes (declared against found)
    3. Size of the data at each step     4. Isolation by platform (method of S2-10)

Run from the project root, after the pipeline:  python -m analysis.s3_08_outputs.make_tables
The first run reads votes_clean.csv twice (about 20 minutes). The counts are saved in two small
files (votes_per_deployment.csv and voters_summary.csv), so later runs take seconds.
"""

import pandas as pd

from src.paths import PROCESSED_DATA_DIR as PROCESSED, RAW_DATA_DIR as RAW, RESULTS_DIR
from src.pipeline.edge_generator import DEFAULT_MAX_DAOS, load_unique_voter_dao_pairs

OUT = RESULTS_DIR / "S3-08"
PLATFORMS = ["snapshot", "tally", "realms", "daohaus", "aragon", "daostack"]


def count_votes_per_deployment():
    """Vote rows of each deployment, counted in votes_clean.csv chunk by chunk."""
    total = None
    for chunk in pd.read_csv(PROCESSED / "votes_clean.csv", usecols=["deployment_id", "platform"],
                             dtype=str, chunksize=1_000_000):
        part = chunk.groupby(["deployment_id", "platform"]).size()
        total = part if total is None else total.add(part, fill_value=0)
    return total.astype(int).rename("vote_rows").reset_index()


def count_voters(max_daos):
    """Distinct (voter, DAO) pairs and voters, with the same pairs the pipeline uses for the edges."""
    pairs = load_unique_voter_dao_pairs().dropna(subset=["voter"])
    daos_per_voter = pairs.groupby("voter").size()
    counts = {"distinct_voter_dao_pairs": len(pairs),
              "distinct_voters": len(daos_per_voter),
              "voters_in_one_dao": (daos_per_voter == 1).sum(),
              f"voters_in_2_to_{max_daos}_daos": daos_per_voter.between(2, max_daos).sum(),
              f"voters_in_more_than_{max_daos}_daos": (daos_per_voter > max_daos).sum()}
    return pd.Series(counts, name="value").astype(int).rename_axis("metric").reset_index()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "votes_per_deployment.csv").exists():
        count_votes_per_deployment().to_csv(OUT / "votes_per_deployment.csv", index=False)
    if not (OUT / "voters_summary.csv").exists():
        count_voters(DEFAULT_MAX_DAOS).to_csv(OUT / "voters_summary.csv", index=False)

    votes = pd.read_csv(OUT / "votes_per_deployment.csv", dtype={"deployment_id": str})
    voters = pd.read_csv(OUT / "voters_summary.csv").set_index("metric")["value"]
    deployments = pd.read_csv(RAW / "deployments.csv", usecols=["platform", "votes_count"])
    proposals = pd.read_csv(RAW / "proposals.csv", usecols=["platform"])
    nodes = pd.read_csv(PROCESSED / "nodes.csv", usecols=["deployment_id", "platform", "in_catalogue"], dtype={"deployment_id": str})
    edges = pd.read_csv(PROCESSED / "edges.csv", dtype={"source": str, "target": str})
    n_jaccard = len(pd.read_csv(PROCESSED / "edges_jaccard.csv", usecols=["source"]))

    # Table 1: rows per file and platform
    t1 = pd.DataFrame({"deployments": deployments.groupby("platform").size(),
                       "proposals": proposals.groupby("platform").size(),
                       "votes": votes.groupby("platform")["vote_rows"].sum()}).reindex(PLATFORMS)
    t1.loc["total"] = t1.sum()

    # Table 2: votes declared in deployments.csv against votes found in votes.csv
    t2 = pd.DataFrame({"declared": deployments.groupby("platform")["votes_count"].sum(),
                       "rows_in_votes_csv": t1["votes"]}).reindex(PLATFORMS)
    t2.loc["total"] = t2.sum()
    t2["coverage_pct"] = (100 * t2["rows_in_votes_csv"] / t2["declared"]).round(1)
    t2[["declared", "rows_in_votes_csv"]] = t2[["declared", "rows_in_votes_csv"]].astype(int)

    # Table 3: size of the data after each step of the pipeline
    connected = set(edges["source"]) | set(edges["target"])
    t3 = pd.DataFrame([
        ("1. votes.csv", "vote rows", t1.loc["total", "votes"]),
        ("2. (voter, DAO) pairs", "distinct pairs", voters["distinct_voter_dao_pairs"]),
        ("2. (voter, DAO) pairs", "distinct voters", voters["distinct_voters"]),
        (f"3. Filter max_daos = {DEFAULT_MAX_DAOS}", f"voters excluded (more than {DEFAULT_MAX_DAOS} DAOs)", voters[f"voters_in_more_than_{DEFAULT_MAX_DAOS}_daos"]),
        (f"3. Filter max_daos = {DEFAULT_MAX_DAOS}", "voters in one DAO only (no edges)", voters["voters_in_one_dao"]),
        (f"3. Filter max_daos = {DEFAULT_MAX_DAOS}", "voters that create edges", voters[f"voters_in_2_to_{DEFAULT_MAX_DAOS}_daos"]),
        ("4. Nodes", "nodes", len(nodes)),
        ("4. Nodes", "nodes not in the catalogue", (~nodes["in_catalogue"]).sum()),
        ("5. Edges", "edges", len(edges)),
        ("5. Edges", "total weight (shared voters)", edges["shared_voters"].sum()),
        ("6. Jaccard", "edges with Jaccard weight", n_jaccard),
        ("7. Graph", "connected nodes", len(connected)),
        ("7. Graph", "isolated nodes", len(nodes) - len(connected)),
    ], columns=["step", "measure", "value"])

    # Table 4: isolation by platform (S2-10): connected, votes but no edges, or no votes
    with_votes = set(votes["deployment_id"])
    nodes["status"] = ["connected" if d in connected else "votes_no_edges" if d in with_votes else "no_votes"
                       for d in nodes["deployment_id"]]
    t4 = pd.crosstab(nodes["platform"], nodes["status"]).reindex(PLATFORMS)[["connected", "votes_no_edges", "no_votes"]]
    t4.insert(0, "nodes", t4.sum(axis=1))
    t4.loc["total"] = t4.sum()
    t4["isolated_among_with_votes_pct"] = (100 * t4["votes_no_edges"] / (t4["connected"] + t4["votes_no_edges"])).round(1)

    for name, table in [("table1_rows_per_file_and_platform", t1), ("table2_votes_coverage", t2),
                        ("table3_graph_size_by_step", t3), ("table4_isolation_by_platform", t4)]:
        table.to_csv(OUT / f"S3-08_{name}.csv", index=name.startswith(("table1", "table2", "table4")))
        print(f"\n{name}\n{table.to_string()}")
