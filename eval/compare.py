#!/usr/bin/env python3
"""Eval script: run multiple models on a single paper and compare outputs field-by-field.

Usage:
    # Multi-model, single prompt (default v3)
    python eval/compare.py --disease copd --paper "#0464_bentley_2014_trimmed.md" --models ds-flash ds-pro

    # Single model, two prompts (prompt-vs-prompt diff)
    python eval/compare.py --disease copd --paper "#0464_..." --models ds-flash --prompt-version v3 v4

    # Multi-model, multi-prompt (all combinations)
    python eval/compare.py --disease copd --paper "#0464_..." --models ds-flash ds-pro --prompt-version v3 v4

    # Skip models/versions already cached
    python eval/compare.py --disease copd --paper "#0464_..." --models ds-flash ds-pro --skip-existing

OpenRouter models: see src/extraction/openrouter_extractor.py -> MODELS

--prompt-version: one or more prompt versions (default: v3). Each model is run once per version.
  Single version -> run key = model name, outputs in output/eval/{version}/.
  Multiple versions -> run key = model@version, diffs/stats in output/eval/ (cross-version).
  Pass '' for the unversioned default prompt.

Per-model prompt overrides (optional): place eval/prompts/{disease}_{model}.md to override
the base prompt for a specific model. Takes precedence over --prompt-version.

Output (single version):
    output/eval/v3/{model}/{cov_nr}.json
    output/eval/v3/diffs/{cov_nr}.json
    output/eval/v3/stats/{cov_nr}.json

Output (multiple versions, e.g. v3 v4):
    output/eval/v3/{model}/{cov_nr}.json
    output/eval/v4/{model}/{cov_nr}.json
    output/eval/diffs/{cov_nr}.json       (cross-version diff)
    output/eval/stats/{cov_nr}.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.llm_utils import _rate_limit
from src.extraction.openrouter_extractor import (
    COST_PER_M as OR_COST_PER_M,
)
from src.extraction.openrouter_extractor import (
    MODELS as OPENROUTER_MODELS,
)
from src.extraction.openrouter_extractor import ExtractionResult
from src.extraction.openrouter_extractor import extract as openrouter_extract
from src.extraction.paper_loader import get_papers

EVAL_DIR = Path(__file__).parent.parent / "output" / "eval"
EVAL_PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

ALL_MODELS: dict[str, str] = OPENROUTER_MODELS
ALL_COSTS: dict[str, dict[str, float]] = OR_COST_PER_M


def _cost(result: ExtractionResult) -> float:
    prices = ALL_COSTS.get(result.model, {})
    return (
        result.input_tokens * prices.get("input", 0)
        + result.output_tokens * prices.get("output", 0)
        + result.cache_read_tokens * prices.get("cache_read", 0)
        + result.cache_creation_tokens * prices.get("cache_write", 0)
    ) / 1_000_000


def _load_base_prompt(disease: str, version: str | None) -> str:
    if version is None:
        return (PROMPTS_DIR / f"prompt_{disease}.md").read_text()
    path = PROMPTS_DIR / f"prompt_{disease}_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Versioned prompt not found: {path}")
    return path.read_text()


def _load_override_prompt(disease: str, short_name: str) -> str | None:
    p = EVAL_PROMPTS_DIR / f"{disease}_{short_name}.md"
    return p.read_text() if p.exists() else None


def _cov_nr(paper_path: Path) -> str:
    return paper_path.stem.lstrip("#")[:4]


def _eval_out_dir(version: str | None) -> Path:
    return EVAL_DIR / version if version else EVAL_DIR


def _load_cached(short_name: str, cov_nr: str, out_dir: Path) -> ExtractionResult | None:
    """Return a cached ExtractionResult if a successful previous run exists, else None."""
    path = out_dir / short_name / f"{cov_nr}.json"
    if not path.exists():
        return None
    arms = json.loads(path.read_text())
    if any(a.get("completed") in (False, "FALSE", "false") for a in arms):
        return None
    return ExtractionResult(
        arms=arms,
        model=ALL_MODELS[short_name],
        elapsed_s=0.0,
        input_tokens=0,
        output_tokens=0,
        cache_creation_tokens=0,
        cache_read_tokens=0,
    )


def _run_model(short_name: str, paper_path: Path, disease: str, base_prompt: str) -> ExtractionResult:
    model_id = ALL_MODELS[short_name]
    prompt = _load_override_prompt(disease, short_name) or base_prompt
    return openrouter_extract(paper_path, disease, model=model_id, system_prompt=prompt)


def _diff_arms(arms_a: list[dict], arms_b: list[dict]) -> list[dict]:
    def arm_key(arm: dict) -> str:
        return arm.get("arm", "unknown")

    map_a = {arm_key(a): a for a in arms_a}
    map_b = {arm_key(b): b for b in arms_b}
    diffs = []
    for arm_name in sorted(set(map_a) | set(map_b)):
        if arm_name not in map_a:
            diffs.append({"arm": arm_name, "field": "_status", "value_a": "missing", "value_b": "present"})
            continue
        if arm_name not in map_b:
            diffs.append({"arm": arm_name, "field": "_status", "value_a": "present", "value_b": "missing"})
            continue
        a, b = map_a[arm_name], map_b[arm_name]
        for field in sorted(set(a) | set(b)):
            va, vb = a.get(field), b.get(field)
            if va != vb:
                diffs.append({"arm": arm_name, "field": field, "value_a": va, "value_b": vb})
    return diffs


def _diff_table_md(model_a: str, model_b: str, diffs: list[dict]) -> str:
    if not diffs:
        return f"## {model_a} vs {model_b}\n\n_Identical output._\n"
    n = len(diffs)
    lines = [
        f"## {model_a} vs {model_b} ({n} difference{'s' if n != 1 else ''})\n",
        f"| {'ARM':<25} | {'FIELD':<35} | {model_a:<25} | {model_b} |",
        f"|{'-'*27}|{'-'*37}|{'-'*27}|{'-'*20}|",
    ]
    for d in diffs:
        lines.append(
            f"| {d['arm']!s:<25} | {d['field']:<35} | {d['value_a']!s:<25} | {d['value_b']} |",
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Eval: compare model outputs on a single paper")
    parser.add_argument("--disease", required=True, choices=["copd", "cvd", "dm"])
    parser.add_argument("--paper", required=True, help="Paper filename (e.g. '#0464_bentley_2014_trimmed.md')")
    parser.add_argument("--models", nargs="+", required=True, choices=list(ALL_MODELS),
                        help="Model short-names to compare")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Load cached results for models that already ran successfully")
    parser.add_argument("--prompt-version", nargs="+", default=["v3"], metavar="VERSION",
                        help="One or more prompt versions (default: v3). Multiple versions run each "
                             "model once per version. Pass '' for the unversioned default prompt.")
    args = parser.parse_args()

    versions: list[str | None] = [v or None for v in args.prompt_version]
    single_version = len(versions) == 1

    specs: list[tuple[str, str, str | None, Path, str]] = []
    for model in args.models:
        for version in versions:
            key = model if single_version else f"{model}@{version or 'default'}"
            specs.append((key, model, version, _eval_out_dir(version), _load_base_prompt(args.disease, version)))

    papers = get_papers(args.disease)
    matches = [p for p in papers if p.name == args.paper]
    if not matches:
        print(f"Paper '{args.paper}' not found in {args.disease}.", file=sys.stderr)
        sys.exit(1)
    paper = matches[0]
    cov_nr = _cov_nr(paper)

    versions_display = ", ".join(v or "default" for v in versions)
    print(f"\n=== EVAL | {args.disease.upper()} | {paper.name} ===")
    print(f"Prompt version{'s' if not single_version else ''}: {versions_display}")
    print(f"Models: {', '.join(args.models)}\n")

    results: dict[str, ExtractionResult] = {}
    cached_keys: set[str] = set()

    for run_key, short_name, version, out_dir_root, base_prompt in specs:
        if args.skip_existing:
            cached = _load_cached(short_name, cov_nr, out_dir_root)
            if cached is not None:
                results[run_key] = cached
                cached_keys.add(run_key)
                print(f"  [{run_key}] skipped (cached) -- {len(cached.arms)} arm{'s' if len(cached.arms) != 1 else ''}")
                continue

        print(f"  [{run_key}] running ...", end=" ", flush=True)
        result = _run_model(short_name, paper, args.disease, base_prompt)
        results[run_key] = result

        model_out_dir = out_dir_root / short_name
        model_out_dir.mkdir(parents=True, exist_ok=True)
        (model_out_dir / f"{cov_nr}.json").write_text(json.dumps(result.arms, indent=2, ensure_ascii=False))

        ok = all(a.get("completed") not in (False, "FALSE", "false") for a in result.arms)
        cost = _cost(result)
        print(
            f"{'OK' if ok else 'ERR'} {len(result.arms)} arm{'s' if len(result.arms) != 1 else ''} | "
            f"{result.elapsed_s:.1f}s | "
            f"in:{result.input_tokens} out:{result.output_tokens} | "
            f"${cost:.4f}",
        )

    col = max(14, max(len(k) for k in results))
    print("\n  -- Stats --")
    print(f"  {'Run':<{col}} {'Time':>6}  {'Input':>7}  {'Output':>7}  {'Cost':>8}")
    print(f"  {'-'*col} {'-'*6}  {'-'*7}  {'-'*7}  {'-'*8}")
    for run_key, r in results.items():
        if run_key in cached_keys:
            print(f"  {run_key:<{col}} {'cached':>6}  {'--':>7}  {'--':>7}  {'--':>8}")
        else:
            print(
                f"  {run_key:<{col}} {r.elapsed_s:>5.1f}s  "
                f"{r.input_tokens:>7}  {r.output_tokens:>7}  "
                f"${_cost(r):>7.4f}",
            )

    run_keys = list(results)
    all_diff_data = []
    diff_text_sections = [f"# Eval diffs: {paper.name}\n"]

    for i, ka in enumerate(run_keys):
        for kb in run_keys[i + 1:]:
            diffs = _diff_arms(results[ka].arms, results[kb].arms)
            all_diff_data.append({"model_a": ka, "model_b": kb, "diffs": diffs})
            n = len(diffs)
            print(f"\n  -- Diff: {ka} vs {kb} ({n} difference{'s' if n != 1 else ''}) --")
            if diffs:
                print(f"  {'ARM':<25} {'FIELD':<35} {ka:<30} {kb}")
                print(f"  {'-'*25} {'-'*35} {'-'*30} {'-'*20}")
                for d in diffs:
                    print(f"  {d['arm']!s:<25} {d['field']:<35} {d['value_a']!s:<30} {d['value_b']}")
            else:
                print("  (identical)")
            diff_text_sections.append(_diff_table_md(ka, kb, diffs))

    diff_stats_dir = _eval_out_dir(versions[0]) if single_version else EVAL_DIR

    diff_dir = diff_stats_dir / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)
    json_path = diff_dir / f"{cov_nr}.json"
    txt_path = diff_dir / f"{cov_nr}.txt"
    json_path.write_text(json.dumps(all_diff_data, indent=2, ensure_ascii=False))
    txt_path.write_text("\n".join(diff_text_sections))

    spec_by_key = {key: (short_name, version) for key, short_name, version, _, _ in specs}
    stats_records = []
    for run_key, r in results.items():
        short_name, version = spec_by_key[run_key]
        ok = all(a.get("completed") not in (False, "FALSE", "false") for a in r.arms)
        record: dict = {
            "run_key": run_key,
            "model": short_name,
            "model_id": r.model,
            "prompt_version": version,
            "source": "cached" if run_key in cached_keys else "live",
            "ok": ok,
            "n_arms": len(r.arms),
        }
        if run_key not in cached_keys:
            record.update({
                "elapsed_s": round(r.elapsed_s, 2),
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cache_creation_tokens": r.cache_creation_tokens,
                "cache_read_tokens": r.cache_read_tokens,
                "cost_usd": round(_cost(r), 6),
            })
        stats_records.append(record)

    stats_dir = diff_stats_dir / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    stats_path = stats_dir / f"{cov_nr}.json"
    stats_path.write_text(json.dumps(stats_records, indent=2, ensure_ascii=False))

    out_label = str(diff_stats_dir.relative_to(diff_stats_dir.parent.parent))
    print(f"\n  -> Saved to {out_label}/")
    print(f"    diffs/{json_path.name}  (structured diffs)")
    print(f"    diffs/{txt_path.name}  (Markdown table)")
    print(f"    stats/{stats_path.name}  (timing + token counts)")


if __name__ == "__main__":
    main()
