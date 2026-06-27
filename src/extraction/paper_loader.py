from pathlib import Path

from config import DATA_DIR

DISEASES = ("copd", "cvd", "dm")


def get_papers(disease: str, source: str = "all_papers") -> list[Path]:
    """Return sorted list of .md paper paths for a disease from specified source."""
    return sorted((DATA_DIR / source / disease).glob("*.md"))


