# thesis-stats

Unified extraction + analysis pipeline for a systematic evidence map of equity reporting in COPD blended care trials.

Extracts baseline characteristics from 752 clinical papers (65 COPD, 412 CVD, 275 DM) using LLMs, validates extraction quality, and produces thesis figures, tables, and statistical analyses.

## Setup

```bash
git clone git@github.com:willemjvdk/thesis-stats.git
cd thesis-stats
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # add OPENROUTER_API_KEY
```

## Repository structure

```
├── run.py                  # Extraction CLI (main entry point)
├── config.py               # Paths, temperature=0, token costs, parallel config
├── requirements.txt        # Python dependencies
├── pyproject.toml          # pytest + coverage + ruff config
│
├── src/
│   ├── extraction/         # LLM extraction pipeline
│   │   ├── openrouter_extractor.py   # OpenRouter API
│   │   ├── llm_utils.py              # Shared LLM utilities
│   │   ├── types.py                  # ExtractionResult, StudyInfo
│   │   ├── paper_loader.py           # Markdown paper loading
│   │   ├── exporter.py               # JSON/CSV export
│   │   ├── differ.py                 # Field-level run comparison
│   │   └── router.py                 # Disease detection from path
│   ├── analysis/           # Statistical analysis modules
│   │   ├── data_loading.py           # Load, validate, aggregate arm/trial data
│   │   ├── aggregation.py            # Arm-to-trial aggregation, PROGRESS-Plus scoring
│   │   ├── statistics.py             # CI, correlation, VIF, Cook's distance, SMD
│   │   ├── plotting.py               # Figure styling and save_figure
│   │   ├── agreement.py              # Inter-rater agreement (AC1, ICC, Jaccard)
│   │   ├── normalization.py          # Value normalizers per data-type bucket
│   │   ├── loaders.py                # JSONL extraction runs, mapping, gold standard
│   │   └── geography.py              # Country-to-continent mapping
│   └── shared/             # Cross-cutting utilities
│       ├── paths.py                  # ROOT_DIR, DATA_DIR constants
│       └── na_detection.py           # Canonical _is_na()
│
├── notebooks/              # Analysis notebooks (run in order)
│   ├── 00_data_validation.ipynb
│   ├── 01_inter_run_consistency.ipynb
│   ├── 02_human_validation.ipynb
│   ├── 03_analysis.ipynb
│   └── outputs/            # Generated figures and tables
│
├── eval/                   # Post-extraction validation
│   ├── validate.py                 # Main validation CLI
│   ├── sebbaflow_validator/        # Checks, schemas, reporters, review DB
│   ├── compare.py                  # Cross-model comparison
│   ├── export_findings.py          # Findings to CSV
│   └── ...                         # Additional eval scripts
│
├── prompts/                # LLM prompts (versioned per disease)
├── scripts/                # Standalone build scripts
├── data/                   # Papers, processed data, references
│   ├── all_papers/{copd,cvd,dm}/   # 752 Markdown papers
│   ├── processed/                  # arms.csv, trials.csv, data_dictionary.md
│   ├── raw/                        # JSONL extractions, source data
│   └── references/                 # External cohort baseline data
│
└── tests/                  # 196 tests (extraction + analysis + smoke)
```

## Extraction pipeline

```bash
# All diseases, default model (ds-flash)
.venv/bin/python run.py

# Single disease
.venv/bin/python run.py --disease copd

# Specific model
.venv/bin/python run.py --model ds-pro

# Parallel processing (default max: 16 workers)
.venv/bin/python run.py --disease cvd --parallel 8

# Smoke test: N random papers per disease
.venv/bin/python run.py --sample 5 --seed 42

# Skip papers with existing output
.venv/bin/python run.py --disease copd --skip-existing

# Labeled run (separate output dir, same prompt)
.venv/bin/python run.py --disease copd --label rerun1

# Disable auto-rerun (default: 3 total attempts)
.venv/bin/python run.py --disease copd --no-rerun

# Rebuild CSVs from existing JSONs
.venv/bin/python run.py --csv

# Check errors (report only)
.venv/bin/python run.py --disease copd --check-errors
```

Available models: `ds-flash` (default), `ds-pro`, `hy3-preview-free`, `ling-2.6-1t-free`.

Output lands in `output/results/{disease}_{version}/`.

### Two-pass extraction

1. **Pass 1 (Arms)**: Extract study metadata (`n_arms`, `arm_labels`) using `prompt_{disease}_arms.md`
2. **Pass 2 (Full)**: Extract full baseline characteristics using the main prompt

## Analysis pipeline

Run notebooks in order via Jupyter or VS Code:

| # | Notebook | Purpose |
|---|----------|---------|
| 00 | `data_validation` | Load raw extraction, validate structure, produce `arms.csv` + `trials.csv` |
| 01 | `inter_run_consistency` | Quantify LLM extraction agreement between two independent passes (AC1, ICC, Jaccard) |
| 02 | `human_validation` | Three-tier human vs LLM validation (prior extraction, gold standard, spot check) |
| 03 | `analysis` | Baseline comparison, PROGRESS-Plus reporting, digital strategy, H1-H3, sensitivity analyses |

"Restart kernel and run all" produces identical results every time.

## Validation tools

```bash
# Validate extraction JSONs
.venv/bin/python eval/validate.py --disease copd

# Auto-fix issues
.venv/bin/python eval/validate.py --disease copd --fix

# Interactive review
.venv/bin/python eval/validate.py --review 0464

# Export findings to CSV
.venv/bin/python eval/export_findings.py --disease copd --severity ERROR

# Cross-model comparison
.venv/bin/python eval/compare.py --disease copd --paper "#0464_bentley_2014_trimmed.md" --models ds-flash ds-pro
```

## Development

```bash
.venv/bin/pytest                  # Run all 196 tests
.venv/bin/pytest -m "not slow"    # Skip slow tests
.venv/bin/ruff check .            # Lint
```

## Data

Input data files (`data/all_papers/`, `data/processed/`, `data/raw/`, `data/references/`) are included. Output data (`output/results/`, `output/review.sqlite`) is gitignored.

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API access (ds-flash, ds-pro) |

## Author

Willem van der Kuijl, Amsterdam UMC, 2026
