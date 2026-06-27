#!/usr/bin/env python3
"""Entry point for the extraction pipeline (OpenRouter-only).

Usage:
    python run.py                          # all diseases, ds-flash, auto-latest prompt
    python run.py --disease copd           # one disease
    python run.py --disease copd dm        # multiple diseases
    python run.py --model ds-flash        # OpenRouter (default)
    python run.py --model ds-pro          # OpenRouter
    python run.py --prompt-version v3     # specific prompt version
    python run.py --parallel 8            # 8 concurrent workers
    python run.py --timeout 300           # 5 min timeout per API call
    python run.py --sample 5 --seed 42   # smoke-test with 5 random papers per disease
    python run.py --disease copd --paper "#0464_bentley_2014_trimmed.md"
    python run.py --disease copd --prompt-version v11 --label rerun1  # separate output dir for comparison
    python run.py --csv                # rebuild CSVs from existing JSONs only
"""

import argparse
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import IO

from config import LOG_DIR, MAX_CONCURRENT, OUTPUT_DIR, PROMPTS_DIR, REQUEST_TIMEOUT, get_output_dir
from src.extraction.exporter import build_csv, save_json
from src.extraction.llm_utils import set_rate_limit_delay
from src.extraction.openrouter_extractor import (
    COST_PER_M as OR_COST_PER_M,
)
from src.extraction.openrouter_extractor import (
    MODELS as OPENROUTER_MODELS,
)
from src.extraction.openrouter_extractor import ExtractionResult
from src.extraction.openrouter_extractor import StudyInfo
from src.extraction.openrouter_extractor import extract as openrouter_extract
from src.extraction.openrouter_extractor import extract_arms as openrouter_extract_arms
from src.extraction.paper_loader import DISEASES, get_papers
from src.extraction.router import get_disease

ALL_MODELS = OPENROUTER_MODELS
ALL_COSTS = OR_COST_PER_M

# ── error detection ───────────────────────────────────────────────────────────


@dataclass
class ErrorReport:
    disease: str
    total_papers: int
    single_arm: int
    invalid_json: int
    unprocessed: int
    catastrophic_extraction: int = 0
    catastrophic_papers: list = field(default_factory=list)
    elapsed_s: float = 0.0
    cost: float = 0.0


def check_errors(disease: str, output_version: str | None = None) -> ErrorReport:
    """Detect extraction errors in output/{disease}_v*/."""
    version = output_version or _discover_output_version(disease)
    output_dir = get_output_dir(disease, version)
    papers = get_papers(disease, "all_papers")
    total_papers = len(papers)

    single_arm = 0
    invalid_json = 0

    for json_file in output_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) == 1:
                single_arm += 1
        except (json.JSONDecodeError, OSError):
            invalid_json += 1

    processed_nrs = {p.stem.lstrip("#")[:4] for p in papers}
    existing_nrs = {p.stem.replace(".json", "") for p in output_dir.glob("*.json")}
    unprocessed = len(processed_nrs - existing_nrs)

    catastrophic_papers = []
    try:
        import sqlite3 as sqlite_conn
        review_db = Path("output/review.sqlite")
        if review_db.exists() and version:
            conn = sqlite_conn.connect(str(review_db))
            rows = conn.execute("""
                SELECT paper_id, COUNT(*) as cnt
                FROM findings
                WHERE category = 'schema_missing_field' AND status = 'open'
                AND prompt_version = ?
                GROUP BY paper_id
                HAVING cnt >= 5
            """, (version,)).fetchall()
            catastrophic_papers = [r[0] for r in rows]
            conn.close()
    except Exception:
        pass

    return ErrorReport(
        disease=disease,
        total_papers=total_papers,
        single_arm=single_arm,
        invalid_json=invalid_json,
        unprocessed=unprocessed,
        catastrophic_extraction=len(catastrophic_papers),
        catastrophic_papers=catastrophic_papers,
        elapsed_s=0.0,
        cost=0.0,
    )


def check_version_drift(disease: str, prompt_version: str | None, output_version: str | None = None) -> list[dict]:
    """Check if prompt version has changed since last extraction."""
    version = output_version or prompt_version or _discover_output_version(disease)
    output_dir = get_output_dir(disease, version)
    current_version = prompt_version or "auto"

    if prompt_version:
        current_version = prompt_version
    else:
        try:
            system_prompt = _discover_prompt_version(disease)
            for p in PROMPTS_DIR.glob(f"prompt_{disease}_v*.md"):
                if p.read_text() == system_prompt:
                    current_version = p.stem.replace(f"prompt_{disease}_", "")
                    break
        except Exception:
            current_version = "unknown"

    drift_papers = []
    for json_file in output_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if not isinstance(data, list):
            continue

        if data and "_metadata" in data[0]:
            stored_version = data[0]["_metadata"].get("prompt_version", "unknown")
            if stored_version != current_version and stored_version != "unknown":
                drift_papers.append({
                    "cov_nr": data[0].get("cov_nr", json_file.stem),
                    "file": json_file.name,
                    "stored_version": stored_version,
                    "current_version": current_version,
                })

    return drift_papers


def report_errors(report: ErrorReport, log_file: IO | None = None) -> None:
    """Print and log error report."""
    errors = report.single_arm + report.invalid_json + report.unprocessed
    summary = (
        f"  Errors: {errors} "
        f"(single-arm: {report.single_arm}, "
        f"invalid JSON: {report.invalid_json}, "
        f"unprocessed: {report.unprocessed})"
    )
    print(summary)
    _log(log_file, summary.strip())

    if report.catastrophic_extraction > 0:
        cat_line = f"  Catastrophic extractions: {report.catastrophic_extraction} papers (>=5 missing fields):"
        for p in report.catastrophic_papers[:10]:
            p_line = f"    - {p}"
            print(p_line)
            _log(log_file, p_line.strip())
        print(cat_line)
        _log(log_file, cat_line.strip())

    if errors > 0:
        hint = f"  To disable auto-rerun: .venv/bin/python run.py --disease {report.disease} --no-rerun"
        print(hint)
        _log(log_file, hint.strip())


def delete_error_outputs(disease: str, output_version: str | None = None,
                          catastrophic_papers: list[str] | None = None) -> list[Path]:
    """Rename JSON files with extraction errors for debugging, then rerun."""
    version = output_version or _discover_output_version(disease)
    output_dir = get_output_dir(disease, version)
    deleted = []

    if catastrophic_papers is None:
        catastrophic_papers = []
        try:
            import sqlite3
            review_db = Path("output/review.sqlite")
            if review_db.exists():
                conn = sqlite3.connect(str(review_db))
                rows = conn.execute("""
                    SELECT paper_id FROM findings
                    WHERE category = 'schema_missing_field' AND status = 'open'
                    GROUP BY paper_id HAVING COUNT(*) >= 5
                """).fetchall()
                catastrophic_papers = [r[0] for r in rows]
                conn.close()
        except Exception:
            pass

    catastrophic_set = set(catastrophic_papers)

    for json_file in output_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) == 1:
                bak = json_file.with_suffix(".1_arm.bak")
                json_file.rename(bak)
                deleted.append(json_file)
        except (json.JSONDecodeError, OSError):
            json_file.unlink()
            deleted.append(json_file)

    for json_file in output_dir.glob("*.json"):
        stem = json_file.stem
        if stem in catastrophic_set:
            bak = json_file.with_suffix(".catastrophic.bak")
            json_file.rename(bak)
            deleted.append(json_file)

    csv_path = output_dir / f"{disease}.csv"
    if csv_path.exists():
        csv_path.unlink()

    return deleted


def run_with_reruns(
    disease: str,
    model_short: str,
    prompt_version: str | None = None,
    label: str | None = None,
    log_file: IO | None = None,
    max_reruns: int = 1,
    parallel: int = 1,
    timeout: int = REQUEST_TIMEOUT,
    summary_path: Path | None = None,
    sample: int | None = None,
    sample_seed: int | None = None,
) -> None:
    """Run disease and optionally rerun errors. Writes a single combined summary."""
    start_time = datetime.now()
    if prompt_version is None:
        prompt_version = _get_prompt_version_number(disease)
    output_version = f"{prompt_version}_{label}" if label else prompt_version
    combined = {"elapsed_s": 0.0, "input": 0, "output": 0, "cost": 0.0, "skipped": 0, "errors": []}
    total_papers = 0
    total_attempts = 0

    for attempt in range(max_reruns + 1):
        if attempt == 0:
            print(f"\n=== {disease.upper()} (attempt {attempt + 1}) ===")
            _log(log_file, f"=== {disease.upper()} (attempt {attempt + 1}) ===")
            deleted = delete_error_outputs(disease, output_version)
            if deleted:
                print(f"  Deleted {len(deleted)} error JSONs before rerun...")
                _log(log_file, f"Rerun: deleted {len(deleted)} error JSONs before rerun")
        else:
            print(f"\n=== {disease.upper()} -- RERUN attempt {attempt + 1}/{max_reruns + 1} ===")
            _log(log_file, f"=== {disease.upper()} -- RERUN attempt {attempt + 1}/{max_reruns + 1} ===")
            deleted = delete_error_outputs(disease, output_version)
            print(f"  Deleted {len(deleted)} error JSONs, rerunning...")
            _log(log_file, f"Rerun: deleted {len(deleted)} error JSONs, rerunning")

        result = run_disease(
            disease,
            model_short,
            prompt_version=prompt_version,
            label=label,
            overwrite=False,
            log_file=log_file,
            parallel=parallel,
            timeout=timeout,
            final=False,
            sample=sample,
            sample_seed=sample_seed,
        )
        total_attempts += 1
        if attempt == 0:
            papers = get_papers(disease)
            total_papers = len(papers) if not sample else min(len(papers), sample)

        combined["elapsed_s"] += result["elapsed_s"]
        combined["input"] += result["input"]
        combined["output"] += result["output"]
        combined["cost"] += result["cost"]
        combined["skipped"] += result["skipped"]

        if attempt < max_reruns and not sample:
            report = check_errors(disease, output_version)
            errors = report.single_arm + report.invalid_json + report.unprocessed
            if errors == 0:
                break

    end_time = datetime.now()
    rerun_count = total_attempts - 1
    final_report = check_errors(disease, output_version)
    final_errors = final_report.single_arm + final_report.invalid_json + final_report.unprocessed
    combined["errors"] = []
    if final_errors > 0 or final_report.catastrophic_extraction > 0:
        output_dir = get_output_dir(disease, output_version)
        for json_file in output_dir.glob("*.json"):
            try:
                with open(json_file) as fh:
                    data = json.load(fh)
                if isinstance(data, list) and len(data) == 1:
                    combined["errors"].append(f"{json_file.stem} (single arm)")
                elif not isinstance(data, list):
                    combined["errors"].append(f"{json_file.stem} (invalid JSON)")
            except (json.JSONDecodeError, OSError):
                combined["errors"].append(f"{json_file.stem} (invalid JSON)")
        for p in final_report.catastrophic_papers:
            combined["errors"].append(f"{p} (catastrophic extraction -- >=5 missing fields)")
        out_dir = get_output_dir(disease, output_version)
        processed_nrs = {p.stem for p in out_dir.glob("*.json")}
        for p in get_papers(disease):
            cov = _cov_nr(p)
            if cov not in processed_nrs:
                combined["errors"].append(f"{cov} (unprocessed)")

    summary = (
        f"  TOTAL: {combined['elapsed_s']:.1f}s | "
        f"in:{combined['input']} out:{combined['output']} | "
        f"${combined['cost']:.4f}"
    )
    if combined["skipped"] > 0:
        summary += f" | SKIPPED: {combined['skipped']}"
    if combined["errors"]:
        summary += f" | ERRORS: {len(combined['errors'])}"
    print(summary)
    _log(log_file, summary.strip())

    if summary_path:
        successful = total_papers - len(combined["errors"])
        _write_summary(
            summary_path, start_time, end_time, disease.upper(),
            total_papers, successful, len(combined["errors"]), combined["skipped"],
            combined["elapsed_s"], combined["input"], combined["output"],
            combined["cost"], model_short, parallel, combined["errors"], rerun_count,
        )
        print(f"  -> Summary: {summary_path}")

    csv_path = build_csv(disease, output_version)
    if csv_path:
        print(f"  -> CSV: {csv_path}")


def _discover_prompt_version(disease: str) -> str:
    """Find the highest versioned prompt for a disease, falls back to base."""
    base = PROMPTS_DIR / f"prompt_{disease}.md"
    pattern = f"prompt_{disease}_v([0-9]+).md"
    matches: list[tuple[int, Path]] = []
    for p in PROMPTS_DIR.glob(f"prompt_{disease}_v*.md"):
        m = re.match(pattern, p.name)
        if m:
            matches.append((int(m.group(1)), p))
    if matches:
        matches.sort(reverse=True)
        return matches[0][1].read_text()
    if base.exists():
        return base.read_text()
    raise FileNotFoundError(f"No prompt found for {disease}")


# ── helpers ──────────────────────────────────────────────────────────────────

def _discover_output_version(disease: str) -> str | None:
    """Find the highest versioned output directory for a disease."""
    pattern = re.compile(rf"{disease}_v([0-9]+)")
    best_version: int | None = None
    for d in OUTPUT_DIR.glob(f"{disease}_v*"):
        m = pattern.match(d.name)
        if m:
            v = int(m.group(1))
            if best_version is None or v > best_version:
                best_version = v
    if best_version is not None:
        return f"v{best_version}"
    unversioned = OUTPUT_DIR / disease
    if unversioned.exists():
        return None
    return None


def _get_prompt_version_number(disease: str) -> str | None:
    """Extract version number string of the highest versioned prompt for a disease."""
    pattern = re.compile(rf"prompt_{disease}_v([0-9]+)\.md$")
    best: tuple[int, str] | None = None
    for p in PROMPTS_DIR.glob(f"prompt_{disease}_v*.md"):
        m = pattern.match(p.name)
        if m:
            v = int(m.group(1))
            if best is None or v > best[0]:
                best = (v, f"v{m.group(1)}")
    return best[1] if best else None


def _cov_nr(paper_path: Path) -> str:
    """Extract zero-padded 5-char cov_nr from filename, e.g. '#0464_' -> '#0464'."""
    stem = paper_path.stem.lstrip("#")
    return stem[:4]


def _cost(result: ExtractionResult) -> float:
    prices = ALL_COSTS.get(result.model, {})
    return (
        result.input_tokens * prices.get("input", 0)
        + result.output_tokens * prices.get("output", 0)
    ) / 1_000_000


def _stats_str(result: ExtractionResult) -> str:
    cost = _cost(result)
    return (
        f"{result.elapsed_s:.1f}s | "
        f"in:{result.input_tokens} out:{result.output_tokens} | "
        f"${cost:.4f}"
    )


def _log(log_file: IO | None, msg: str) -> None:
    if log_file:
        ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        log_file.write(f"{ts} {msg}\n")
        log_file.flush()


# ── enhanced logging ───────────────────────────────────────────────────────────


def _write_summary(
    summary_path: Path,
    start_time: datetime,
    end_time: datetime,
    disease: str,
    total_papers: int,
    successful: int,
    failed: int,
    skipped: int,
    total_elapsed_s: float,
    input_tokens: int,
    output_tokens: int,
    total_cost: float,
    model: str,
    parallel: int,
    errors: list[str],
    reruns: int,
) -> None:
    """Write human-readable summary file."""
    duration_s = (end_time - start_time).total_seconds()
    minutes = int(duration_s // 60)
    seconds = int(duration_s % 60)

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write("                              RUN SUMMARY\n")
        f.write("================================================================================\n")
        f.write(f"Run started:    {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Run ended:      {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration:      {minutes}m {seconds:02d}s\n")
        f.write(f"Disease:       {disease}\n")
        f.write(f"Papers:        {total_papers} total | {successful} OK | {failed} Error | {skipped} Skipped\n")
        f.write(f"Parallel:      {parallel} workers\n")
        f.write(f"Model:         {model}\n")
        f.write(f"Processing:    {total_elapsed_s:.1f}s total CPU time\n")
        f.write("\n")
        f.write("COSTS\n")
        f.write("--------------------------------------------------------------------------------\n")
        f.write(f"Input tokens:  {input_tokens:,}\n")
        f.write(f"Output tokens: {output_tokens:,}\n")
        f.write(f"Total cost:    ${total_cost:.4f}\n")
        f.write("\n")
        if errors:
            f.write("ERRORS\n")
            f.write("--------------------------------------------------------------------------------\n")
            for err in errors:
                f.write(f"  - {err}\n")
            f.write("\n")
        if reruns > 0:
            f.write("RERUNS\n")
            f.write("--------------------------------------------------------------------------------\n")
            f.write(f"Total reruns:  {reruns}\n")
            f.write("\n")
        f.write("================================================================================\n")


# ── normal run ───────────────────────────────────────────────────────────────

def run_paper(
    paper_path: Path,
    model_short: str,
    model_id: str,
    system_prompt: str,
    prompt_version: str | None = None,
    output_version: str | None = None,
    overwrite: bool = True,
    log_file: IO | None = None,
    timeout: int = REQUEST_TIMEOUT,
    worker_id: int | None = None,
) -> ExtractionResult | None:
    disease = get_disease(paper_path)
    cov_nr = _cov_nr(paper_path)
    output_path = get_output_dir(disease, output_version or prompt_version) / f"{cov_nr}.json"

    if output_path.exists() and not overwrite:
        worker_tag = f"[W{worker_id:02d}]" if worker_id else ""
        print(f"  {worker_tag} {paper_path.name} ... SKIPPED (exists)", flush=True)
        return None

    if output_path.exists() and overwrite:
        response = input(f"  {output_path.name} exists. Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            print("  SKIPPED (user declined)")
            return None

    worker_tag = f"[W{worker_id:02d}]" if worker_id else ""
    _log(log_file, f"[{disease.upper()}] START {paper_path.name} worker={worker_id}")

    # Two-pass extraction: first get arm count, then full extraction
    study_info_dict: dict | None = None
    study_result: StudyInfo = openrouter_extract_arms(paper_path, disease, model=model_id, timeout=timeout)
    if study_result.error is None:
        study_info_dict = {
            "n_arms": study_result.n_arms,
            "arm_labels": study_result.arm_labels,
        }

    result: ExtractionResult = openrouter_extract(paper_path, disease, model=model_id, system_prompt=system_prompt, timeout=timeout)

    save_json(result.arms, disease, cov_nr, output_version or prompt_version, model=model_short, prompt_version=prompt_version, study_info=study_info_dict)

    ok = all(a.get("completed") not in (False, "FALSE", "false") for a in result.arms)
    n_arms = len(result.arms)
    status = "OK" if ok else "ERR"
    stats = _stats_str(result)
    line = f"  {worker_tag} {paper_path.name} ... {status} {n_arms} arm{'s' if n_arms != 1 else ''} | {stats}"
    print(line, flush=True)
    _log(log_file, f"[{disease.upper()}] {paper_path.name} | {line.strip()}")
    return result


def run_disease(
    disease: str,
    model_short: str,
    prompt_version: str | None = None,
    label: str | None = None,
    paper_name: str | None = None,
    sample: int | None = None,
    sample_seed: int | None = None,
    overwrite: bool = True,
    log_file: IO | None = None,
    parallel: int = 1,
    timeout: int = REQUEST_TIMEOUT,
    summary_path: Path | None = None,
    final: bool = True,
    reruns: int = 0,
) -> dict:
    """Run extraction for a disease. Returns totals dict."""
    papers = get_papers(disease)
    if paper_name:
        papers = [p for p in papers if p.name == paper_name]
        if not papers:
            print(f"Paper '{paper_name}' not found in {disease}.", file=sys.stderr)
            sys.exit(1)
    if sample:
        if sample_seed is not None:
            papers = sorted(papers)
            random.Random(sample_seed).shuffle(papers)
        papers = papers[:sample] if sample else papers

    parallel_mode = parallel > 1
    if parallel_mode:
        header = f"\n=== {disease.upper()} ({len(papers)} papers, {parallel} workers, model: {model_short}, prompt: {prompt_version or 'auto'}, timeout: {timeout}s) ==="
    else:
        header = f"\n=== {disease.upper()} ({len(papers)} paper{'s' if len(papers) != 1 else ''}, model: {model_short}, prompt: {prompt_version or 'auto'}) ==="

    print(header)
    _log(log_file, header.strip())

    system_prompt = _discover_prompt_version(disease) if prompt_version is None else (
        (PROMPTS_DIR / f"prompt_{disease}_{prompt_version}.md").read_text()
        if (PROMPTS_DIR / f"prompt_{disease}_{prompt_version}.md").exists()
        else (PROMPTS_DIR / f"prompt_{disease}.md").read_text()
    )

    if prompt_version is None:
        pattern = re.compile(rf"prompt_{disease}_v([0-9]+)\.md$")
        for p in sorted(PROMPTS_DIR.glob(f"prompt_{disease}_v*.md"), reverse=True):
            m = pattern.match(p.name)
            if m:
                if p.read_text() == system_prompt:
                    prompt_version = f"v{m.group(1)}"
                    break
    output_version = f"{prompt_version}_{label}" if label else prompt_version
    model_id = ALL_MODELS[model_short]

    set_rate_limit_delay(parallel)

    start_time = datetime.now()
    totals = {"elapsed_s": 0.0, "input": 0, "output": 0, "cost": 0.0, "skipped": 0}
    errors = []

    if parallel_mode:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {}
            for idx, paper in enumerate(papers):
                worker_id = (idx % parallel) + 1
                future = executor.submit(
                    run_paper,
                    paper, model_short, model_id, system_prompt,
                    prompt_version, output_version, overwrite, log_file, timeout, worker_id,
                )
                futures[future] = (paper, worker_id)

            for future in as_completed(futures):
                paper, worker_id = futures[future]
                try:
                    r = future.result()
                    if r is not None:
                        totals["elapsed_s"] += r.elapsed_s
                        totals["input"] += r.input_tokens
                        totals["output"] += r.output_tokens
                        totals["cost"] += _cost(r)
                        if not all(a.get("completed") not in (False, "FALSE", "false") for a in r.arms):
                            errors.append(f"{paper.name} (worker {worker_id})")
                    else:
                        totals["skipped"] += 1
                except Exception as e:
                    errors.append(f"{paper.name} (worker {worker_id}): {e}")
                    _log(log_file, f"[ERROR] {paper.name}: {e}")
    else:
        for paper in papers:
            r = run_paper(paper, model_short, model_id, system_prompt, prompt_version, output_version, overwrite, log_file, timeout)
            if r is not None:
                totals["elapsed_s"] += r.elapsed_s
                totals["input"] += r.input_tokens
                totals["output"] += r.output_tokens
                totals["cost"] += _cost(r)
                if not all(a.get("completed") not in (False, "FALSE", "false") for a in r.arms):
                    errors.append(paper.name)
            else:
                totals["skipped"] += 1

    end_time = datetime.now()

    if len(papers) > 1 and final:
        summary = (
            f"  TOTAL: {totals['elapsed_s']:.1f}s | "
            f"in:{totals['input']} out:{totals['output']} | "
            f"${totals['cost']:.4f}"
        )
        if totals["skipped"] > 0:
            summary += f" | SKIPPED: {totals['skipped']}"
        if errors:
            summary += f" | ERRORS: {len(errors)}"
        print(summary)
        _log(log_file, summary.strip())

    if final and summary_path:
        successful = len(papers) - len(errors)
        failed = len(errors)
        _write_summary(
            summary_path, start_time, end_time, disease.upper(),
            len(papers), successful, failed, totals["skipped"],
            totals["elapsed_s"], totals["input"], totals["output"],
            totals["cost"], model_short, parallel, errors, reruns,
        )
        print(f"  -> Summary: {summary_path}")

    csv_path = build_csv(disease, output_version)
    if csv_path:
        print(f"  -> CSV: {csv_path}")

    return {
        "elapsed_s": totals["elapsed_s"],
        "input": totals["input"],
        "output": totals["output"],
        "cost": totals["cost"],
        "skipped": totals["skipped"],
        "errors": errors,
    }


# ── entry point ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Medical paper extraction pipeline")
    parser.add_argument("--disease", nargs="+", choices=[*DISEASES, "all"], default=["all"])
    parser.add_argument("--model", choices=list(ALL_MODELS), default="ds-flash", help="Model (default: ds-flash)")
    parser.add_argument("--prompt-version", help="Prompt version (e.g. v3). Auto-detects latest if omitted")
    parser.add_argument("--paper", help="Process a specific paper filename only")

    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip papers with existing JSON output")
    parser.add_argument("--check-errors", action="store_true",
                        help="Run error detection and report (no extraction)")
    parser.add_argument("--max-reruns", type=int, default=2,
                        help="Max rerun attempts (default: 2)")
    parser.add_argument("--no-rerun", action="store_true",
                        help="Disable auto-rerun (one-shot run)")
    parser.add_argument("--parallel", type=int, default=1,
                        help=f"Number of parallel workers (default: 1, max: {MAX_CONCURRENT})")
    parser.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT,
                        help=f"API call timeout in seconds (default: {REQUEST_TIMEOUT})")
    parser.add_argument("--check-version-drift", action="store_true",
                        help="Check if prompt version changed since last extraction")
    parser.add_argument("--label", help="Output dir label -- appended as suffix, e.g. --label rerun1 -> copd_v11_rerun1/")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sample", type=int, help="Run first N papers per disease for smoke-testing")
    parser.add_argument("--seed", type=int, help="Random seed for --sample (deterministic shuffle)")
    mode.add_argument("--csv", action="store_true", help="Rebuild CSVs from existing JSONs without re-extracting")

    args = parser.parse_args()

    if args.parallel > MAX_CONCURRENT:
        print(f"Warning: --parallel {args.parallel} exceeds MAX_CONCURRENT ({MAX_CONCURRENT}). Using {MAX_CONCURRENT}.")
        args.parallel = MAX_CONCURRENT
    if args.parallel < 1:
        args.parallel = 1

    diseases = DISEASES if "all" in args.disease else tuple(args.disease)
    overwrite = not args.skip_existing

    if args.csv:
        for d in diseases:
            out_ver = f"{args.prompt_version}_{args.label}" if (args.label and args.prompt_version) else args.prompt_version
            csv_path = build_csv(d, out_ver)
            print(f"{d}: {csv_path or 'no results found'}")
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"run_{timestamp}.log"
    summary_path = LOG_DIR / f"run_{timestamp}.summary"
    print(f"Logging to {log_path}")
    print(f"Summary will be saved to {summary_path}")

    if args.check_version_drift:
        print("\n=== Version Drift Check ===")
        total_drift = 0
        for d in diseases:
            out_ver = f"{args.prompt_version}_{args.label}" if (args.label and args.prompt_version) else None
            drifts = check_version_drift(d, args.prompt_version, output_version=out_ver)
            if drifts:
                total_drift += len(drifts)
                print(f"\n{d.upper()}: {len(drifts)} papers with version drift")
                for drift in drifts:
                    print(f"  - {drift['cov_nr']}: stored={drift['stored_version']}, current={drift['current_version']}")
            else:
                print(f"{d.upper()}: OK (no drift detected)")
        print(f"\n{'='*40}")
        if total_drift > 0:
            print(f"ERROR: {total_drift} papers have prompt version drift!")
            print("Run extraction with a new prompt version to update.")
            print("Use --prompt-version to specify the version, or the latest will be auto-detected.")
            sys.exit(1)
        else:
            print("No version drift detected. Safe to proceed.")
        return

    if args.check_errors:
        with log_path.open("w", encoding="utf-8") as log_file:
            for d in diseases:
                out_ver = f"{args.prompt_version}_{args.label}" if (args.label and args.prompt_version) else None
                report = check_errors(d, output_version=out_ver)
                report_errors(report, log_file)
        return

    with log_path.open("w", encoding="utf-8") as log_file:
        for d in diseases:
            disease_summary = LOG_DIR / f"run_{timestamp}_{d}.summary"

            if args.no_rerun:
                run_disease(
                    d,
                    model_short=args.model,
                    prompt_version=args.prompt_version,
                    label=args.label,
                    paper_name=args.paper,
                    sample=args.sample,
                    sample_seed=args.seed,
                    overwrite=overwrite,
                    log_file=log_file,
                    parallel=args.parallel,
                    timeout=args.timeout,
                    summary_path=disease_summary,
                )
                out_ver = f"{args.prompt_version}_{args.label}" if (args.label and args.prompt_version) else None
                report = check_errors(d, output_version=out_ver)
                report_errors(report, log_file)
            else:
                run_with_reruns(
                    d,
                    model_short=args.model,
                    prompt_version=args.prompt_version,
                    label=args.label,
                    log_file=log_file,
                    max_reruns=args.max_reruns,
                    parallel=args.parallel,
                    timeout=args.timeout,
                    summary_path=disease_summary,
                    sample=args.sample,
                    sample_seed=args.seed,
                )

    print("\n" + "="*80)
    print("                              RUN SUMMARY")
    print("="*80)
    for d in diseases:
        disease_summary = LOG_DIR / f"run_{timestamp}_{d}.summary"
        if disease_summary.exists():
            print(disease_summary.read_text())
    print("="*80)


if __name__ == "__main__":
    main()
