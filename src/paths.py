"""
Single definition of the project folders.

Every module imports its paths from here instead of computing them from
its own location, so moving a file to another folder never breaks the
paths again.
"""

from pathlib import Path

# src/paths.py -> parents[0] is src/, parents[1] is the repository root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "docs" / "figures"
