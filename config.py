from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent
PROMPTS_DIR = ROOT_DIR / "prompts"
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output" / "results"
LOG_DIR = ROOT_DIR / "output" / "results" / "logs"


def get_output_dir(disease: str, version: str | None = None) -> Path:
    """Return output directory. With version: output/results/{disease}_{version}/.
    Without version: output/results/{disease}/."""
    if version:
        return ROOT_DIR / "output" / "results" / f"{disease}_{version}"
    return OUTPUT_DIR / disease


COMPARE_DIR = OUTPUT_DIR / "compare"

TEMPERATURE = 0
assert TEMPERATURE == 0, "temperature must be 0 for reproducibility"
MAX_TOKENS = 4096

# Parallel processing config
MAX_CONCURRENT = 16  # Max parallel workers for API calls
REQUEST_TIMEOUT = 300  # 5 minutes timeout per API call
