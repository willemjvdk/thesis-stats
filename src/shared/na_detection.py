import math
from typing import Any

NA_TOKENS = frozenset({
    "na", "n/a", "na ", " n/a", "n a", "not reported",
    "not available", "not applicable", "nr", "nr.", "n.r.", "none",
    "missing", "unk", "unknown", "-", "–", "—", ".", "..", "...",
})


def _is_na(value: Any) -> bool:
    """Detect any value that should be treated as missing."""
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or value != value):
        return True
    if isinstance(value, str) and value.strip().lower() in NA_TOKENS:
        return True
    if isinstance(value, list):
        if len(value) == 0:
            return True
        if (len(value) == 1 and isinstance(value[0], str)
                and value[0].strip().lower() in NA_TOKENS):
            return True
    try:
        if isinstance(value, float) and math.isnan(value):
            return True
    except TypeError:
        pass
    return False
