from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result from a single extraction run (arm-level fields)."""
    arms: list[dict]
    model: str
    elapsed_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class StudyInfo:
    """Result from study-level (arms) extraction."""
    cov_nr: str
    n_arms: int
    arm_labels: list[str]
    model: str = ""
    elapsed_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
