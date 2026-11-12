import csv
from collections import Counter

from src.paths import PROCESSED_DATA_DIR, RESULTS_DIR


PLATFORMS = {"snapshot", "aragon", "daohaus", "daostack"}
OUTPUT = RESULTS_DIR / "S3-11"


def read_rows(filename):
    with (PROCESSED_DATA_DIR / filename).open(
        encoding="utf-8", newline=""
    ) as file:
        return list(csv.DictReader(file))


def read_edges(filename, weight_column):
    edges = {}
    for row in read_rows(filename):
        pair = tuple(sorted((row["source"], row["target"])))
        weight = int(row[weight_column])
        if pair[0] == pair[1] or pair in edges or weight <= 0:
            raise ValueError(f"Invalid or repeated edge in {filename}: {pair}")
        edges[pair] = weight
    return edges


def save(filename, rows):
    if not rows:
        return
    with (OUTPUT / filename).open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def overlap(scope, voters, authors):
    common = voters & authors
    return {
        "scope": scope,
        "voter_edges": len(voters),
        "author_edges": len(authors),
        "common_edges": len(common),
        "voter_only": len(voters - authors),
        "author_only": len(authors - voters),
        "pct_author_edges_in_voters": 100 * len(common) / len(authors),
        "pct_voter_edges_in_authors": 100 * len(common) / len(voters),
    }


def node_metrics(pairs, weights):
    degree = Counter()
    strength = Counter()
    for pair in pairs:
        for node in pair:
            degree[node] += 1
            strength[node] += weights[pair]
    return {"degree": degree, "strength": strength}


def ranking(values):
    return sorted(values, key=lambda node: (-values[node], node))


def main():
    voters = read_edges("edges.csv", "shared_voters")
    authors = read_edges("edges_authors.csv", "shared_authors")
    node_rows = read_rows("nodes.csv")
    nodes = {row["deployment_id"]: row for row in node_rows}

    if len(nodes) != len(node_rows):
        raise ValueError("Repeated deployment identifiers in nodes.csv")

    endpoints = {node for pair in voters.keys() | authors.keys() for node in pair}
    missing = endpoints - nodes.keys()
    if missing:
        raise ValueError(f"Edge endpoints missing from nodes.csv: {sorted(missing)}")

    # Ensure that the inputs match the documented v5 reference totals.
    actual = (len(voters), sum(voters.values()),
              len(authors), sum(authors.values()))
    expected = (700304, 10682356, 28359, 37919)
    if actual != expected:
        raise ValueError(f"Unexpected input totals: {actual}; expected {expected}")

    covered = {
        node for node, row in nodes.items()
        if row["platform"] in PLATFORMS
    }
    restricted_voters = {
        pair for pair in voters if set(pair) <= covered
    }
    restricted_authors = {
        pair for pair in authors if set(pair) <= covered
    }

    summaries = [
        overlap("all", set(voters), set(authors)),
        overlap("covered_platforms", restricted_voters, restricted_authors),
    ]
    common = restricted_voters & restricted_authors

    def platform_pair(pair):
        return " - ".join(sorted(nodes[node]["platform"] for node in pair))

    voter_counts = Counter(map(platform_pair, restricted_voters))
    author_counts = Counter(map(platform_pair, restricted_authors))
    common_counts = Counter(map(platform_pair, common))
    platform_rows = []
    for pair in sorted(voter_counts.keys() | author_counts.keys()):
        denominator = author_counts[pair]
        platform_rows.append({
            "platform_pair": pair,
            "voter_edges": voter_counts[pair],
            "author_edges": denominator,
            "common_edges": common_counts[pair],
            "pct_author_edges_in_voters":
                100 * common_counts[pair] / denominator if denominator else "",
        })

    voter_metrics = node_metrics(restricted_voters, voters)
    author_metrics = node_metrics(restricted_authors, authors)
    rankings = {}
    ranking_rows = []

    for network, metrics in [
        ("voters", voter_metrics), ("authors", author_metrics)
    ]:
        for measure, values in metrics.items():
            ordered = ranking(values)
            rankings[(network, measure)] = ordered
            for position, node in enumerate(ordered, start=1):
                ranking_rows.append({
                    "network": network,
                    "measure": measure,
                    "rank": position,
                    "deployment_id": node,
                    "name": nodes[node]["name"],
                    "platform": nodes[node]["platform"],
                    "value": values[node],
                })

    rank_overlap = []
    for measure in ["degree", "strength"]:
        for k in [10, 50, 100]:
            shared = (
                set(rankings[("voters", measure)][:k])
                & set(rankings[("authors", measure)][:k])
            )
            rank_overlap.append({
                "measure": measure, "k": k, "common_nodes": len(shared)
            })

    voter_nodes = set(voter_metrics["degree"])
    author_nodes = set(author_metrics["degree"])
    connected = [{
        "scope": "covered_platforms",
        "voter_nodes": len(voter_nodes),
        "author_nodes": len(author_nodes),
        "common_nodes": len(voter_nodes & author_nodes),
        "voter_only": len(voter_nodes - author_nodes),
        "author_only": len(author_nodes - voter_nodes),
    }]

    examples = []
    categories = [
        ("common_by_authors", common, authors),
        ("author_only", restricted_authors - restricted_voters, authors),
        ("voter_only", restricted_voters - restricted_authors, voters),
    ]
    for category, pairs, weights in categories:
        selected = sorted(pairs, key=lambda pair: (-weights[pair], pair))[:3]
        for source, target in selected:
            pair = (source, target)
            examples.append({
                "category": category,
                "source": source,
                "target": target,
                "shared_voters": voters.get(pair, 0),
                "shared_authors": authors.get(pair, 0),
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    save("edge_overlap.csv", summaries)
    save("overlap_by_platform.csv", platform_rows)
    save("node_rankings.csv", ranking_rows)
    save("ranking_overlap.csv", rank_overlap)
    save("connected_nodes.csv", connected)
    save("relationship_examples.csv", examples)

    for row in summaries:
        print(
            f"{row['scope']}: "
            f"{row['common_edges']:,} common edges; "
            f"{row['voter_only']:,} voter-only; "
            f"{row['author_only']:,} author-only"
        )
    print(f"Saved six result tables to {OUTPUT}")


if __name__ == "__main__":
    main()