from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

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

    return nodes

#Export
def save_dao_nodes(nodes):
    output_file = PROCESSED_DATA_DIR / "nodes.csv"

    nodes.to_csv(output_file, index=False)
if __name__ == "__main__":
    nodes = generate_dao_nodes()
    save_dao_nodes(nodes)

    print(f"Nodes generated: {len(nodes)}")
    