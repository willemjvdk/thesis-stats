import csv
import json
import sys
from datetime import datetime
from pathlib import Path

from config import get_output_dir


def _serialize(value) -> str:
    if isinstance(value, list):
        return "~".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def _ordered_fieldnames(records: list[dict]) -> list[str]:
    """Union of all keys across records, preserving first-seen order."""
    seen: dict[str, None] = {}
    for record in records:
        seen.update(dict.fromkeys(record.keys()))
    return list(seen)


def save_json(
    arms: list[dict],
    disease: str,
    cov_nr: str,
    version: str | None = None,
    overwrite: bool = True,
    model: str | None = None,
    prompt_version: str | None = None,
    study_info: dict | None = None,
) -> Path:
    """Write per-paper extraction to output/results/{disease}_[{version}/]{cov_nr}.json."""
    out_dir = get_output_dir(disease, version)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{cov_nr}.json"

    # Add metadata to each arm
    metadata = {
        "prompt_version": prompt_version or version or "unknown",
        "model": model or "unknown",
        "extracted_at": datetime.now().isoformat(),
    }
    if study_info:
        metadata["study_info"] = study_info
    for arm in arms:
        arm["_metadata"] = metadata

    if path.exists() and not overwrite:
        return path
    path.write_text(json.dumps(arms, indent=2, ensure_ascii=False))
    return path


def build_csv(disease: str, version: str | None = None) -> Path | None:
    in_dir = get_output_dir(disease, version)
    if not in_dir.exists():
        return None

    records: list[dict] = []
    invalid_count = 0
    for json_file in sorted(in_dir.glob("*.json")):
        try:
            records.extend(json.loads(json_file.read_text()))
        except json.JSONDecodeError:
            invalid_count += 1
            print(f"  Skipping invalid JSON: {json_file.name}", file=sys.stderr)

    if not records:
        return None

    if invalid_count > 0:
        print(f"  Skipped {invalid_count} invalid JSON files", file=sys.stderr)

    csv_path = in_dir / f"{disease}.csv"
    fieldnames = _ordered_fieldnames(records)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({k: _serialize(row.get(k)) for k in fieldnames})

    return csv_path
