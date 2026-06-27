import json
import os
import time
from pathlib import Path

import openai

from config import REQUEST_TIMEOUT, TEMPERATURE
from src.extraction.llm_utils import (
    _load_arms_prompt,
    _load_prompt,
    _parse_response,
    _rate_limit,
    get_rate_limit_delay,
    set_rate_limit_delay,
)
from src.extraction.types import ExtractionResult, StudyInfo

# Higher than the global MAX_TOKENS — OpenRouter models generate verbose output
MAX_TOKENS = 16384

_RETRY_DELAYS = (1, 2, 4)

# Short-name → OpenRouter model slug. Verify/update at openrouter.ai/models.
MODELS: dict[str, str] = {
    "ds-flash":      "deepseek/deepseek-v4-flash",       # DeepSeek V3-flash
    "hy3-preview-free": "tencent/hy3-preview:free",
    "ds-pro":        "deepseek/deepseek-v4-pro",          # DeepSeek V4-pro (reasoning)
    "ling-2.6-1t-free":   "inclusionai/ling-2.6-1t:free",
}

# USD per million tokens (verified 2026-05-02 at openrouter.ai)
COST_PER_M: dict[str, dict[str, float]] = {
    "deepseek/deepseek-v4-flash": {"input": 0.14,    "output": 0.28,   "cache_read": 0.0028},
    "deepseek/deepseek-v4-pro":   {"input": 0.435,   "output": 0.87,   "cache_read": 0.003625},
    "tencent/hy3-preview:free":   {"input": 0.00,    "output": 0.00},
    "inclusionai/ling-2.6-1t:free": {"input": 0.00,  "output": 0.00},
}

_client: openai.OpenAI | None = None


def _get_client(timeout: int = REQUEST_TIMEOUT) -> openai.OpenAI:
    global _client
    if _client is None:
        if "OPENROUTER_API_KEY" not in os.environ:
            raise RuntimeError(
                "OPENROUTER_API_KEY not set in environment. "
                "Add it to .env to use OpenRouter models (ds-flash, ds-pro, etc).",
            )
        _client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            timeout=timeout,
        )
    return _client


def _api_call_with_retry(client: openai.OpenAI, model: str, system_prompt: str, user_message: str) -> openai.ChatCompletion:
    """Make API call with retry on transient errors."""
    last_error: Exception | None = None
    for attempt in range(len(_RETRY_DELAYS) + 1):
        try:
            return client.chat.completions.create(
                model=model,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
        except Exception as exc:
            last_error = exc
            should_retry = (
                hasattr(exc, "type") and exc.type == "rate_limit_error"
            ) or (hasattr(exc, "status") and exc.status in (429, 500, 502, 503, 504))
            if should_retry and attempt < len(_RETRY_DELAYS):
                time.sleep(_RETRY_DELAYS[attempt])
                continue
            raise
    raise last_error from None


def extract(
    paper_path: Path,
    disease: str,
    model: str,
    system_prompt: str | None = None,
    timeout: int = REQUEST_TIMEOUT,
) -> ExtractionResult:
    """Call OpenRouter for one paper; return an ExtractionResult with arms and usage stats."""
    _rate_limit()

    prompt = system_prompt if system_prompt is not None else _load_prompt(disease)
    paper_text = paper_path.read_text()
    user_message = f"Filename: {paper_path.name}\n\n{paper_text}"
    client = _get_client(timeout)

    t0 = time.perf_counter()
    raw = ""
    try:
        response = _api_call_with_retry(client, model, prompt, user_message)
        elapsed = time.perf_counter() - t0
        usage = response.usage
        raw = response.choices[0].message.content or ""
        arms = _parse_response(raw)
        if not arms:
            raise ValueError(f"No JSON objects found in response: {raw[:200]!r}")
        return ExtractionResult(
            arms=arms,
            model=model,
            elapsed_s=elapsed,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        error_msg = f"{exc}"
        if raw:
            error_msg = f"{exc} | response: {raw[:200]!r}"
        return ExtractionResult(
            arms=[{"completed": False, "error": error_msg, "paper": str(paper_path)}],
            model=model,
            elapsed_s=elapsed,
            input_tokens=0,
            output_tokens=0,
            cache_creation_tokens=0,
            cache_read_tokens=0,
        )


def extract_arms(
    paper_path: Path,
    disease: str,
    model: str,
    timeout: int = REQUEST_TIMEOUT,
) -> StudyInfo:
    """Extract only study design metadata (n_arms, arm_labels) using arms prompt."""
    _rate_limit()

    prompt = _load_arms_prompt(disease)
    paper_text = paper_path.read_text()
    user_message = f"Filename: {paper_path.name}\n\n{paper_text}"
    client = _get_client(timeout)

    t0 = time.perf_counter()
    raw = ""
    try:
        response = _api_call_with_retry(client, model, prompt, user_message)
        elapsed = time.perf_counter() - t0
        usage = response.usage
        raw = response.choices[0].message.content or ""

        parsed = json.loads(raw.strip())
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected dict, got {type(parsed).__name__}")

        cov_nr = parsed.get("cov_nr", paper_path.stem.lstrip("#")[:4])
        n_arms = parsed.get("n_arms", 0)
        arm_labels = parsed.get("arm_labels", [])

        return StudyInfo(
            cov_nr=str(cov_nr),
            n_arms=int(n_arms) if n_arms else 0,
            arm_labels=arm_labels if isinstance(arm_labels, list) else [],
            model=model,
            elapsed_s=elapsed,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )
    except Exception as exc:
        elapsed = time.perf_counter() - t0
        error_msg = f"{exc}"
        if raw:
            error_msg = f"{exc} | response: {raw[:200]!r}"
        return StudyInfo(
            cov_nr=paper_path.stem.lstrip("#")[:4],
            n_arms=0,
            arm_labels=[],
            model=model,
            elapsed_s=elapsed,
            input_tokens=0,
            output_tokens=0,
            error=error_msg,
        )
