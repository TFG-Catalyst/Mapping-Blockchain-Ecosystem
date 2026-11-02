import pandas as pd

from src.paths import PROCESSED_DATA_DIR
from src.pipeline.data_loader import load_deployments, load_proposals, load_votes
from src.pipeline.wallet_normalization import extract_address


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
    output_dir = PROCESSED_DATA_DIR

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
    """
    Clean votes.csv chunk by chunk and append each clean chunk to
    data/processed/votes_clean.csv, so the whole file is never in memory.

    Returns (rows_read, rows_written). clean_votes() only transforms columns
    and never drops rows, so both numbers must be equal.
    """
    output_dir = PROCESSED_DATA_DIR
    output_file = output_dir / "votes_clean.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    first_chunk = True
    rows_read = 0
    rows_written = 0

    for i, chunk in enumerate(votes_generator, start=1):
        rows_read += len(chunk)
        cleaned_chunk = clean_votes(chunk)

        cleaned_chunk.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False
        rows_written += len(cleaned_chunk)

        print(f"Chunk {i} processed - {len(cleaned_chunk)} rows "
              f"(total {rows_written:,})")

    return rows_read, rows_written


def run_cleaning():
    """
    Clean the three raw CSVs of data/raw/ and write the clean versions to
    data/processed/ (deployments_clean.csv, proposals_clean.csv and
    votes_clean.csv). Same steps as cells 60 and 61 of notebook 02.
    """
    print("Cleaning deployments and proposals")
    deployments_clean = clean_deployments(load_deployments())
    proposals_clean = clean_proposals(load_proposals())
    save_processed_data(deployments_clean, proposals_clean)
    print(f"  deployments: {len(deployments_clean)} rows, "
          f"proposals: {len(proposals_clean)} rows")

    print("Cleaning votes (in chunks)")
    rows_read, rows_written = process_votes(load_votes())
    print(f"  votes: {rows_read:,} rows read, {rows_written:,} rows written")
    if rows_read != rows_written:
        raise ValueError(
            f"Votes lost while cleaning: read {rows_read}, wrote {rows_written}"
        )


if __name__ == "__main__":
    run_cleaning()