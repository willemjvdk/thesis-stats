from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_REFERENCES = DATA_DIR / "references"
DATA_ALL_PAPERS = DATA_DIR / "all_papers"
