import json
import re
import time
from pathlib import Path

from config import PROMPTS_DIR

_PROMPT_FILES = {
    "copd": PROMPTS_DIR / "prompt_copd_v11.md",
    "cvd": PROMPTS_DIR / "prompt_cvd_v9.md",
    "dm": PROMPTS_DIR / "prompt_dm_v10.md",
}

_ARMS_PROMPT_FILES = {
    "copd": PROMPTS_DIR / "prompt_copd_arms.md",
    "cvd": PROMPTS_DIR / "prompt_cvd_arms.md",
    "dm": PROMPTS_DIR / "prompt_dm_arms.md",
}

_RETRY_DELAYS = (1, 2, 4)
_BASE_RATE_LIMIT_DELAY = 1.0
_rate_limit_delay = _BASE_RATE_LIMIT_DELAY


def set_rate_limit_delay(parallel: int) -> None:
    """Set rate limit delay based on parallel workers."""
    global _rate_limit_delay
    if parallel > 1:
        _rate_limit_delay = _BASE_RATE_LIMIT_DELAY / parallel
    else:
        _rate_limit_delay = _BASE_RATE_LIMIT_DELAY


def get_rate_limit_delay() -> float:
    """Get current rate limit delay."""
    return _rate_limit_delay


def _rate_limit() -> None:
    time.sleep(_rate_limit_delay)


def _load_prompt(disease: str) -> str:
    return _PROMPT_FILES[disease].read_text()


def _load_arms_prompt(disease: str) -> str:
    return _ARMS_PROMPT_FILES[disease].read_text()


def _parse_response(text: str) -> list[dict]:
    text = re.sub(r"```(?:json)?\n?", "", text).strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        pass
    objects: list[dict] = []
    depth = 0
    start: int | None = None
    for i, ch in enumerate(text):
        if ch == "{" and depth == 0:
            start = i
            depth = 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    obj = json.loads(text[start : i + 1])
                    objects.append(obj)
                except json.JSONDecodeError:
                    pass
                start = None
    return objects
