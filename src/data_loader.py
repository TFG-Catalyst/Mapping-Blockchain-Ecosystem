from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def _check_file_exists(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )


def load_deployments():
    file_path = RAW_DATA_DIR / "deployments.csv"
    _check_file_exists(file_path)

    return pd.read_csv(file_path)


def load_proposals():
    file_path = RAW_DATA_DIR / "proposals.csv"
    _check_file_exists(file_path)

    return pd.read_csv(file_path)


def load_votes(chunksize=1_000_000):
    file_path = RAW_DATA_DIR / "votes.csv"
    _check_file_exists(file_path)

    return pd.read_csv(
        file_path,
        chunksize=chunksize
    )