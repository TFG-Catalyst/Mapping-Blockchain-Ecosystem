from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

def find_uncatalogued_deployments(catalogue_ids, chunksize=1_000_000):
    # Deployments that have votes in votes_clean.csv but no row in the catalogue
    file_path = PROCESSED_DATA_DIR / "votes_clean.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed votes file not found: {file_path}"
        )

    chunks = []

    for chunk in pd.read_csv(
        file_path,
        usecols=["deployment_id", "platform"],
        dtype=str,
        keep_default_na=False,
        chunksize=chunksize
    ):
        chunk = chunk.drop_duplicates()
        chunks.append(chunk[~chunk["deployment_id"].isin(catalogue_ids)])

    uncatalogued = pd.concat(chunks, ignore_index=True).drop_duplicates()

    if uncatalogued["deployment_id"].duplicated().any():
        raise ValueError(
            "An uncatalogued deployment appears with more than one platform"
        )

    return uncatalogued

def generate_dao_nodes():
    file_path = PROCESSED_DATA_DIR / "deployments_clean.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed deployments file not found: {file_path}"
        )

    deployments = pd.read_csv(file_path)

    node_columns = [
        "deployment_id",
        "platform",
        "name",
        "proposals_count",
        "unique_voters",
        "votes_count"
    ]

    nodes = deployments[node_columns].copy()
    nodes["in_catalogue"] = True

    uncatalogued = find_uncatalogued_deployments(set(nodes["deployment_id"]))
    uncatalogued["in_catalogue"] = False

    nodes = pd.concat([nodes, uncatalogued], ignore_index=True)

    return nodes

#Export
def save_dao_nodes(nodes):
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    output_file = PROCESSED_DATA_DIR / "nodes.csv"
    nodes.to_csv(output_file, index=False)
if __name__ == "__main__":
    nodes = generate_dao_nodes()
    save_dao_nodes(nodes)

    print(f"Nodes generated: {len(nodes)}")
    print(f"Nodes not in catalogue: {(~nodes['in_catalogue']).sum()}")
    