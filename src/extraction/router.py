from pathlib import Path

from src.extraction.paper_loader import DISEASES


def get_disease(paper_path: Path) -> str:
    """Infer disease type from the paper's parent directory name (copd/cvd/dm)."""
    name = paper_path.parent.name
    if name not in DISEASES:
        raise ValueError(f"Unknown disease directory '{name}' for paper: {paper_path}")
    return name
