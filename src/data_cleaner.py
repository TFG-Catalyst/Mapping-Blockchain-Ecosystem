import pandas as pd
from pathlib import Path

try:
    from .wallet_normalization import extract_address
except ImportError:  # run as a script from src/
    from wallet_normalization import extract_address


def clean_deployments(df):
    #working on a copy to conserve the raw data
    df = df.copy()
    #Normalize deployment IDs for a consistent format (lowercase strings)
    df["deployment_id"] = (
        df["deployment_id"]
        .astype("string")
        .str.lower()
    )

    return df

def clean_proposals(df):
    #Same as before, working on a copy to conserve the raw data
    df = df.copy()
    # Normalize deployment_id  to lowercase strings
    df["deployment_id"] = (
        df["deployment_id"]
        .astype("string")
        .str.lower()
    )

    # Normalize platform_deployment_id to lowercase strings
    df["platform_deployment_id"] = (
        df["platform_deployment_id"]
        .astype("string")
        .str.lower()
    )
    # Using deployment_id as the primary identifier, fill missing dao_id values with platform_deployment_id
    df["dao_id"] = df["deployment_id"].fillna(
    df["platform_deployment_id"]
    )
    #remove duplicate rows based on all columns to ensure data integrity
    df = df.drop_duplicates()

    return df
def normalize_voter(voter, platform=None):
    # Preserve missing voter values
    if pd.isna(voter):
        return pd.NA

    # The format is detected from the value itself (see wallet_normalization.py).
    # `platform` is kept only so that old calls normalize_voter(voter, platform)
    # keep working; it does not change the result.
    return extract_address(str(voter))


def clean_votes(df):
    df = df.copy()

    df["deployment_id"] = (
        df["deployment_id"]
        .astype("string")
        .str.lower()
    )

    df["voter"] = [
        normalize_voter(voter, platform)
        for voter, platform in zip(df["voter"], df["platform"])
    ]

    return df

def save_processed_data(deployments, proposals):
    output_dir = Path(__file__).resolve().parents[1] / "data" / "processed"

    output_dir.mkdir(parents=True, exist_ok=True)

    deployments.to_csv(
        output_dir / "deployments_clean.csv",
        index=False
    )

    proposals.to_csv(
        output_dir / "proposals_clean.csv",
        index=False
    )

def process_votes(votes_generator):
    output_dir = Path(__file__).resolve().parents[1] / "data" / "processed"
    output_file = output_dir / "votes_clean.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    first_chunk = True

    for i, chunk in enumerate(votes_generator, start=1):
        cleaned_chunk = clean_votes(chunk)

        cleaned_chunk.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

        print(f"Chunk {i} processed - {len(cleaned_chunk)} rows")