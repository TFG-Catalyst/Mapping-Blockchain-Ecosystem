import pandas as pd

from src.paths import RAW_DATA_DIR

# Columns read as text. pandas reads votes.csv in chunks and guesses the type
# of each chunk separately, so an id could be a number in one chunk and a
# string in another. date and weight are also kept as text, so the clean files
# keep them exactly as in the raw files (a float would round very large
# voting-power values).
DEPLOYMENTS_DTYPES = {"deployment_id": str}
PROPOSALS_DTYPES = {
    "proposal_id": str,
    "deployment_id": str,
    "platform_deployment_id": str,
    "author": str,
    "date": str,
}
VOTES_DTYPES = {
    "vote_id": str,
    "proposal_id": str,
    "deployment_id": str,
    "voter": str,
    "date": str,
    "choice": str,
    "weight": str,
}


def _check_file_exists(file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {file_path}"
        )


def load_deployments():
    file_path = RAW_DATA_DIR / "deployments.csv"
    _check_file_exists(file_path)

    return pd.read_csv(file_path, dtype=DEPLOYMENTS_DTYPES)


def load_proposals():
    file_path = RAW_DATA_DIR / "proposals.csv"
    _check_file_exists(file_path)

    return pd.read_csv(file_path, dtype=PROPOSALS_DTYPES)


def load_votes(chunksize=1_000_000):
    file_path = RAW_DATA_DIR / "votes.csv"
    _check_file_exists(file_path)

    return pd.read_csv(
        file_path,
        dtype=VOTES_DTYPES,
        chunksize=chunksize
    )