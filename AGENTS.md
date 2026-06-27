# AGENTS.md — thesis-stats

## Critical commands

- **Always use `.venv/bin/python`**, not system Python
- **Linter**: `.venv/bin/ruff check .`
- **Tests**: `.venv/bin/pytest` (196 tests; skip slow with `-m "not slow"`)
- **Coverage**: `.venv/bin/pytest --cov`

## Key conventions

- `temperature=0` is enforced on all API calls — asserted in `config.py`
- Prompts in `prompts/` are versioned (`_v*.md`); auto-discovers highest version
- Paper filenames start with `#` (e.g., `#0464_bentley_2014_trimmed.md`)
- Output lands in `output/results/{disease}_{version}/`
- Logs in `output/results/logs/` (`.log` verbose, `.summary` human-readable)

## Import conventions

```python
# Analysis modules
from src.analysis.data_loading import load_arms
from src.analysis.aggregation import arm_weighted_mean_per_trial
from src.analysis.statistics import compute_smd_table
from src.analysis.plotting import save_figure

# Extraction modules
from src.extraction.openrouter_extractor import extract
from src.extraction.types import ExtractionResult

# Shared utilities
from src.shared.paths import ROOT_DIR, DATA_DIR

# Eval (self-contained, only within eval/)
from eval.sebbaflow_validator.checks import run_all_checks
```

**Note**: Notebook import cells must use `src.analysis.X`, not `src.X`. The flat path `src.data_loading` does not exist — code lives at `src/analysis/data_loading.py`.

## Notebook editing rules

**Sub-agents may EXPLORE notebooks (read, grep, search) but must NEVER edit or write .ipynb files.** Cell indices shift on every insert — only nbformat running locally can safely handle this.

1. Read the notebook to understand the problem.
2. Write a local Python script using **nbformat** to read → modify → write.
3. Run the script: `python scripts/_nb_edit.py`
4. Run the validator: `python scripts/validate_notebook.py --check notebooks/<name>.ipynb`
5. Delete `_nb_edit.py` when done.

### Styling conventions

- Per-cell "what and why" comments, not per-line docstrings
- Import cells: group `src/` modules with 1-line summaries
- Final cell: timestamp + schema hash reference + key counts only
- Validation: `print` warnings, not `assert`

## Data layout

```
data/
├── all_papers/{copd,cvd,dm}/   # 752 Markdown papers (source corpus)
├── processed/                   # arms.csv, trials.csv, country_year.csv, data_dictionary.md
├── raw/                         # JSONL extractions, source spreadsheets
└── references/                  # External cohort baseline data (Adelphi, ECLIPSE, Nijmegen)
```

## Extraction pipeline

Two-pass extraction via `run.py`:

1. **Pass 1 (Arms)**: Extract `n_arms`, `arm_labels` using `prompt_{disease}_arms.md`
2. **Pass 2 (Full)**: Extract full baseline characteristics using the main prompt

### Key flags

| Flag | Purpose |
|------|---------|
| `--disease {copd,cvd,dm,all}` | Target disease(s) |
| `--model ds-flash` | OpenRouter model (default: ds-flash) |
| `--parallel N` | Concurrent workers (max: 16; delay scales as 1s/N) |
| `--sample N --seed S` | Random sample of N papers per disease |
| `--skip-existing` | Skip papers with existing JSON output |
| `--label NAME` | Separate output dir for run comparison |
| `--no-rerun` | Disable auto-rerun (default: up to 2 reruns) |
| `--timeout SECS` | API call timeout (default: 300s) |
| `--csv` | Rebuild CSVs from existing JSONs without re-extracting |
| `--check-errors` | Report errors only, no extraction |
| `--prompt-version v3` | Override prompt version (auto-discovers latest if omitted) |

### Error detection

Detected by `run.py`: single arm, invalid JSON, unprocessed paper, catastrophic extraction (5+ missing fields).
Detected by `eval/validate.py`: arm count mismatch, cross-arm time inconsistency, schema missing field.

## Validation tools

### validate.py CLI

```bash
.venv/bin/python eval/validate.py --disease copd              # validate all papers
.venv/bin/python eval/validate.py --paper 0464                # single paper
.venv/bin/python eval/validate.py --fix                       # auto-fix
.venv/bin/python eval/validate.py --review 0464               # interactive review
.venv/bin/python eval/validate.py --accept 0464 3             # accept finding #3
.venv/bin/python eval/validate.py --reject 0464 5 "reason"    # reject finding #5
.venv/bin/python eval/validate.py --stats                     # review dashboard
.venv/bin/python eval/validate.py --apply-reviewed path.csv   # apply CSV decisions
```

### Auto-fix rules

- Value-based fixes (set missing required fields)
- Field renames (`instrument_name` -> `health_literacy_instrument_name`)
- Field removals (`gender_intermediate_n`, `gender_intermediate_pct`)
- Array sum fixes (sum < arm n: infer missing categories; sum > arm n: flag)

### Export findings

```bash
.venv/bin/python eval/export_findings.py                                    # all findings
.venv/bin/python eval/export_findings.py --disease copd --severity ERROR    # filtered
.venv/bin/python eval/export_findings.py --status open                      # open only
```

Review DB: `output/review.sqlite` (SQLite, open in DB browser for review dashboard).

## Cross-model comparison

```bash
.venv/bin/python eval/compare.py \
  --disease copd \
  --paper "#0464_bentley_2014_trimmed.md" \
  --models ds-flash ds-pro
```

Output: `output/eval/v3/{model}/{cov_nr}.json` + structured diffs.

## Run comparison

```bash
# First run
.venv/bin/python run.py --disease copd

# Second run with label (same prompt, separate output dir)
.venv/bin/python run.py --disease copd --label rerun1

# Compare CSVs
diff output/results/copd/copd.csv output/results/copd_rerun1/copd.csv
```

## Author

Willem van der Kuijl, Amsterdam UMC, 2026
